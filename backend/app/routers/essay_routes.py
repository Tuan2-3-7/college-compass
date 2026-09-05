from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user
from ..database import get_db
from ..models import Application, Essay, EssayDraft, EssayFeedback, User
from ..schemas import DraftIn, DraftOut, EssayIn, EssayOut, FeedbackOut
from ..services.llm import get_llm

router = APIRouter(prefix="/api/essays", tags=["essays"])


def _owned_essay(db: Session, user: User, essay_id: int) -> Essay:
    essay = (
        db.query(Essay)
        .options(joinedload(Essay.drafts).joinedload(EssayDraft.feedback))
        .filter(Essay.id == essay_id, Essay.user_id == user.id)
        .first()
    )
    if essay is None:
        raise HTTPException(status_code=404, detail="Essay not found")
    return essay


@router.get("", response_model=list[EssayOut])
def list_essays(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Essay)
        .options(joinedload(Essay.drafts).joinedload(EssayDraft.feedback))
        .filter(Essay.user_id == user.id)
        .order_by(Essay.created_at.desc())
        .all()
    )


@router.post("", response_model=EssayOut, status_code=201)
def create_essay(data: EssayIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.application_id is not None:
        owned = (
            db.query(Application)
            .filter(Application.id == data.application_id, Application.user_id == user.id)
            .first()
        )
        if owned is None:
            raise HTTPException(status_code=404, detail="Application not found")
    essay = Essay(user_id=user.id, **data.model_dump())
    db.add(essay)
    db.commit()
    db.refresh(essay)
    return essay


@router.get("/{essay_id}", response_model=EssayOut)
def get_essay(essay_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _owned_essay(db, user, essay_id)


@router.delete("/{essay_id}", status_code=204)
def delete_essay(essay_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    essay = _owned_essay(db, user, essay_id)
    db.delete(essay)
    db.commit()


@router.post("/{essay_id}/drafts", response_model=DraftOut, status_code=201)
def add_draft(
    essay_id: int, data: DraftIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    essay = _owned_essay(db, user, essay_id)
    version = (essay.drafts[-1].version + 1) if essay.drafts else 1
    draft = EssayDraft(essay_id=essay.id, version=version, content=data.content)
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/{essay_id}/drafts/{draft_id}/analyze", response_model=FeedbackOut)
def analyze_draft(
    essay_id: int,
    draft_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    essay = _owned_essay(db, user, essay_id)
    draft = next((d for d in essay.drafts if d.id == draft_id), None)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    llm = get_llm()
    try:
        result = llm.analyze_essay(essay.prompt, draft.content, essay.word_limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # replace any previous feedback for this draft
    if draft.feedback is not None:
        db.delete(draft.feedback)
        db.flush()
    feedback = EssayFeedback(
        draft_id=draft.id,
        overall_score=result["overall_score"],
        scores=result["scores"],
        paragraph_feedback=result["paragraph_feedback"],
        weaknesses=result["weaknesses"],
        suggestions=result["suggestions"],
        questions=result["questions"],
        flags=result.get("flags", {}),
        provider=result["provider"],
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
