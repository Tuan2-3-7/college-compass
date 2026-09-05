from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user
from ..database import get_db
from ..models import Application, Scholarship, StudentProfile, Task, User
from ..services.checklist import resolve_deadline

router = APIRouter(prefix="/api", tags=["financial-aid"])


def _scholarship_dict(s: Scholarship) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "provider": s.provider,
        "amount_max": s.amount_max,
        "renewable": s.renewable,
        "eligibility": s.eligibility,
        "min_gpa": s.min_gpa,
        "majors": s.majors,
        "deadline": s.deadline,
        "deadline_note": s.deadline_note,
        "description": s.description,
        "source_url": s.source_url,
        "data_source": s.data_source,
        "last_verified": s.last_verified.isoformat() if s.last_verified else None,
    }


@router.get("/scholarships")
def list_scholarships(
    db: Session = Depends(get_db),
    eligibility: str | None = Query(default=None, pattern="^(domestic|international)$"),
    major: str | None = None,
    min_amount: int | None = None,
):
    query = db.query(Scholarship)
    results = query.all()
    if eligibility:
        results = [s for s in results if s.eligibility in (eligibility, "both")]
    if major:
        needle = major.lower().replace(" ", "_")
        results = [s for s in results if not s.majors or needle in s.majors]
    if min_amount is not None:
        results = [s for s in results if s.amount_max is None or s.amount_max >= min_amount]
    results.sort(key=lambda s: (s.deadline is None, s.deadline or ""))
    return [_scholarship_dict(s) for s in results]


@router.get("/financial-aid/plan")
def financial_aid_plan(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Personalized aid plan: forms per school on the list + matching scholarships."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    applications = (
        db.query(Application)
        .options(joinedload(Application.university))
        .filter(Application.user_id == user.id)
        .all()
    )
    aid_tasks = (
        db.query(Task)
        .filter(Task.user_id == user.id, Task.category == "financial_aid")
        .order_by(Task.due_date.is_(None), Task.due_date)
        .all()
    )

    is_intl = profile is not None and profile.student_type == "international"
    needs_aid = profile is not None and profile.financial_aid_needed

    # ---- forms ----
    forms = []
    if needs_aid:
        if is_intl:
            forms.append({
                "name": "University financial aid forms (CSS Profile or ISFAA)",
                "who": "Schools that offer aid to international students",
                "note": "Each school chooses its own form - check the aid page of every school on your list.",
            })
            forms.append({
                "name": "Proof of funds / financial certification",
                "who": "Every school, after admission",
                "note": "Bank statements and sponsor letters covering year one - needed for the I-20 regardless of aid.",
            })
        else:
            forms.append({
                "name": "FAFSA",
                "who": "Every US school",
                "note": "File at studentaid.gov as early as possible and add each school's code.",
            })
            forms.append({
                "name": "CSS Profile",
                "who": "~200 mostly-private schools",
                "note": "Required for institutional aid at many privates - check each school's aid page.",
            })

    # ---- per-school aid picture (sample data - verify) ----
    schools = []
    for app in applications:
        uni = app.university
        aid_deadline = resolve_deadline(uni.deadlines or {}, "regular")
        schools.append({
            "university": uni.name,
            "offers_intl_aid": uni.offers_intl_aid,
            "intl_support_notes": uni.intl_support_notes,
            "cost_of_attendance": uni.cost_of_attendance,
            "application_deadline": app.deadline.isoformat() if app.deadline else None,
            "aid_hint": (
                "Aid forms are typically due at or before the admission deadline"
                + (f" (~{aid_deadline.isoformat()})" if aid_deadline else "")
                + " - verify on the school's aid page."
            ),
        })

    # ---- scholarship matches ----
    scholarships = db.query(Scholarship).all()
    matches = []
    if profile is not None:
        student_kind = "international" if is_intl else "domestic"
        for s in scholarships:
            if s.eligibility not in (student_kind, "both"):
                continue
            if s.min_gpa is not None and profile.gpa is not None and profile.gpa_scale:
                if (profile.gpa / profile.gpa_scale) * 4.0 < s.min_gpa - 0.01:
                    continue
            if s.majors and profile.intended_major and profile.intended_major not in s.majors:
                continue
            matches.append(_scholarship_dict(s))
        matches.sort(key=lambda s: (s["deadline"] is None, s["deadline"] or ""))

    return {
        "needs_aid": needs_aid,
        "student_type": profile.student_type if profile else None,
        "forms": forms,
        "schools": schools,
        "scholarships": matches,
        "aid_tasks": [
            {
                "id": t.id, "title": t.title, "status": t.status,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
            for t in aid_tasks
        ],
        "disclaimer": (
            "Each scholarship shows whether it was checked against the sponsor's own site "
            "and when. Amounts and deadlines change every year, so confirm on the official "
            "page before applying - especially anything marked unverified."
        ),
    }
