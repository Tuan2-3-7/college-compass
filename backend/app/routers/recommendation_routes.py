from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import settings
from ..database import get_db
from ..models import User
from ..services.llm import get_llm
from ..services.recommendations import build_recommendations

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/recommendations")
def recommendations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_recommendations(db, user)


@router.get("/ai/status")
def ai_status():
    """Which AI provider is active - the UI shows a demo-mode badge for mock."""
    llm = get_llm()
    model = None
    if llm.name == "anthropic":
        model = settings.anthropic_model
    elif llm.name in ("openai_compat", "ollama"):
        model = getattr(llm, "model", None)
    return {"provider": llm.name, "model": model}
