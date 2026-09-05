from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..data.international import DISCLAIMER, PATHWAY_STAGES
from ..database import get_db
from ..models import Application, StudentProfile, User

router = APIRouter(prefix="/api/international", tags=["international"])


@router.get("/pathway")
def pathway(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    applicable = profile is not None and profile.student_type == "international"

    applications = db.query(Application).filter(Application.user_id == user.id).all()
    any_submitted = any(a.status in ("submitted", "decision_received") for a in applications)
    any_accepted = any(a.decision == "accepted" for a in applications)

    # infer the student's current stage from application state
    if any_accepted:
        current = "financial_documentation"
    elif any_submitted:
        current = "admission"
    else:
        current = "application"

    keys = [s["key"] for s in PATHWAY_STAGES]
    current_index = keys.index(current)
    stages = [
        {
            **stage,
            "status": (
                "done" if i < current_index else "current" if i == current_index else "upcoming"
            ),
        }
        for i, stage in enumerate(PATHWAY_STAGES)
    ]

    return {
        "applicable": applicable,
        "current_stage": current,
        "stages": stages,
        "disclaimer": DISCLAIMER,
        "note": None if applicable else (
            "Your profile is set to domestic - this pathway applies to international "
            "students on F-1 visas. Update your profile if that's you."
        ),
    }
