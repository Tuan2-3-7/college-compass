from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user
from ..database import get_db
from ..models import Application, StudentProfile, University, User
from ..services.analyzer import profile_scores, university_fit

router = APIRouter(prefix="/api/analyzer", tags=["analyzer"])


def _profile(db: Session, user: User) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Complete your profile first")
    return profile


@router.get("/profile")
def analyze_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """School-independent competitiveness subscores + overall."""
    return profile_scores(_profile(db, user))


@router.get("/applications")
def analyze_applications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Reach/Target/Likely for every university on the student's list."""
    profile = _profile(db, user)
    apps = (
        db.query(Application)
        .options(joinedload(Application.university))
        .filter(Application.user_id == user.id)
        .all()
    )
    return [
        {"application_id": app.id, **university_fit(profile, app.university)} for app in apps
    ]


@router.get("/university/{university_id}")
def analyze_university(
    university_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Fit vs any university (doesn't need to be on the list)."""
    university = db.get(University, university_id)
    if university is None:
        raise HTTPException(status_code=404, detail="University not found")
    return university_fit(_profile(db, user), university)
