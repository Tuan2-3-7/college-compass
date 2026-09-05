from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..data.majors import MAJORS
from ..database import get_db
from ..models import StudentProfile, User
from ..services.major_advisor import advisor_payload

router = APIRouter(prefix="/api/majors", tags=["majors"])


@router.get("")
def list_majors():
    return [{"key": key, "label": data["label"]} for key, data in MAJORS.items()]


@router.get("/{major_key}/advisor")
def major_advisor(
    major_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Roadmap for a major, personalized with the student's skill-gap analysis."""
    if major_key not in MAJORS:
        raise HTTPException(status_code=404, detail=f"Unknown major. Available: {sorted(MAJORS)}")
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Complete your profile first")
    return advisor_payload(profile, major_key)
