from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import TutorMessage, User
from ..services.llm import get_llm

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@router.get("/history")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = (
        db.query(TutorMessage)
        .filter(TutorMessage.user_id == user.id)
        .order_by(TutorMessage.created_at, TutorMessage.id)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


@router.post("/chat")
def chat(data: ChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    past = (
        db.query(TutorMessage)
        .filter(TutorMessage.user_id == user.id)
        .order_by(TutorMessage.created_at, TutorMessage.id)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in past]

    result = get_llm().tutor_reply(data.message, history)

    db.add(TutorMessage(user_id=user.id, role="user", content=data.message))
    db.add(TutorMessage(user_id=user.id, role="assistant", content=result["reply"]))
    db.commit()
    return result


@router.delete("/history", status_code=204)
def clear_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(TutorMessage).filter(TutorMessage.user_id == user.id).delete()
    db.commit()
