from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Application, StudentProfile, University, User
from ..services.analyzer import university_fit

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("")
def compare(
    ids: str = Query(description="Comma-separated university ids, 2-4 of them"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        id_list = [int(x) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=422, detail="ids must be comma-separated integers")
    if not 2 <= len(id_list) <= 4:
        raise HTTPException(status_code=422, detail="Compare 2 to 4 universities")

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    my_apps = {
        a.university_id: a
        for a in db.query(Application).filter(Application.user_id == user.id).all()
    }

    columns = []
    for uid in id_list:
        uni = db.get(University, uid)
        if uni is None:
            raise HTTPException(status_code=404, detail=f"University {uid} not found")
        fit = university_fit(profile, uni) if profile else None
        app = my_apps.get(uid)
        columns.append({
            "id": uni.id,
            "name": uni.name,
            "location": f"{uni.city}, {uni.state}",
            "control": uni.control,
            "undergrad_enrollment": uni.undergrad_enrollment,
            "acceptance_rate": uni.acceptance_rate,
            "sat_range": f"{uni.sat_25}-{uni.sat_75}" if uni.sat_25 else None,
            "test_policy": uni.test_policy,
            "cost_of_attendance": uni.cost_of_attendance,
            "tuition_in_state": uni.tuition_in_state,
            "toefl_min": uni.toefl_min,
            "offers_intl_aid": uni.offers_intl_aid,
            "supplemental_essay_count": uni.supplemental_essay_count,
            "application_fee": uni.application_fee,
            "deadlines": uni.deadlines,
            "majors": uni.majors,
            "classification": fit["classification"] if fit else None,
            "on_list": uid in my_apps,
            "my_round": app.round if app else None,
            "my_deadline": app.deadline.isoformat() if app and app.deadline else None,
            "data_source": uni.data_source,
        })

    return {
        "universities": columns,
        "disclaimer": "Sample data - unverified. Fit labels are heuristic estimates, not predictions.",
    }
