from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user
from ..database import get_db
from ..models import Application, StudentProfile, Task, User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

PROFILE_FIELDS = [
    "full_name", "gpa", "intended_major", "courses", "activities",
]


def _profile_completeness(profile: StudentProfile | None) -> int:
    if profile is None:
        return 0
    filled = 0
    for field in PROFILE_FIELDS:
        value = getattr(profile, field)
        if value not in (None, "", [], {}):
            filled += 1
    # tests count as one slot; international students may legitimately have none,
    # so TOEFL/IELTS also counts
    if profile.sat or profile.act or profile.toefl or profile.ielts:
        filled += 1
    return round(filled / (len(PROFILE_FIELDS) + 1) * 100)


@router.get("")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    applications = (
        db.query(Application)
        .options(joinedload(Application.university))
        .filter(Application.user_id == user.id)
        .all()
    )
    tasks = db.query(Task).filter(Task.user_id == user.id).all()

    today = date.today()
    soon = today + timedelta(days=30)

    open_tasks = [t for t in tasks if t.status != "done"]
    due_soon = sorted(
        (t for t in open_tasks if t.due_date and today <= t.due_date <= soon),
        key=lambda t: t.due_date,
    )
    overdue = sorted(
        (t for t in open_tasks if t.due_date and t.due_date < today), key=lambda t: t.due_date
    )

    app_summaries = []
    for app in applications:
        app_tasks = [t for t in tasks if t.application_id == app.id]
        done = sum(1 for t in app_tasks if t.status == "done")
        total = len(app_tasks)
        app_summaries.append(
            {
                "id": app.id,
                "university": app.university.name,
                "round": app.round,
                "status": app.status,
                "deadline": app.deadline.isoformat() if app.deadline else None,
                "days_left": (app.deadline - today).days if app.deadline else None,
                "tasks_done": done,
                "tasks_total": total,
                "progress": round(done / total * 100) if total else 0,
            }
        )
    app_summaries.sort(key=lambda a: (a["days_left"] is None, a["days_left"]))

    total_tasks = len(tasks)
    done_tasks = sum(1 for t in tasks if t.status == "done")

    # "What should I do next?" (rule-based for Phase 1; AI-assisted in Phase 3)
    next_action = None
    if profile is None or _profile_completeness(profile) < 50:
        next_action = {
            "title": "Complete your student profile",
            "reason": "Your profile drives checklists and (later) competitiveness analysis.",
        }
    elif not applications:
        next_action = {
            "title": "Add your first university",
            "reason": "Use the University Finder to build your college list.",
        }
    elif overdue:
        t = overdue[0]
        next_action = {
            "title": t.title,
            "reason": f"This task was due {t.due_date.isoformat()} and is overdue.",
            "task_id": t.id,
        }
    elif due_soon:
        t = due_soon[0]
        next_action = {
            "title": t.title,
            "reason": f"Due {t.due_date.isoformat()} - your nearest deadline.",
            "task_id": t.id,
        }

    return {
        "profile_completeness": _profile_completeness(profile),
        "applications": app_summaries,
        "tasks_total": total_tasks,
        "tasks_done": done_tasks,
        "tasks_overdue": [
            {"id": t.id, "title": t.title, "due_date": t.due_date.isoformat()} for t in overdue[:10]
        ],
        "tasks_due_soon": [
            {"id": t.id, "title": t.title, "due_date": t.due_date.isoformat()} for t in due_soon[:10]
        ],
        "next_action": next_action,
    }
