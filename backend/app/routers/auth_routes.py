from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import Essay, Notification, StudentProfile, TutorMessage, User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, hashed_password=hash_password(data.password))
    db.add(user)
    db.flush()
    # every user starts with an empty profile
    db.add(StudentProfile(user_id=user.id))
    db.commit()
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenOut(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.delete("/me", status_code=204)
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete the account and every piece of the student's data (privacy requirement)."""
    db.query(Notification).filter(Notification.user_id == user.id).delete()
    db.query(TutorMessage).filter(TutorMessage.user_id == user.id).delete()
    for essay in db.query(Essay).filter(Essay.user_id == user.id).all():
        db.delete(essay)  # cascades drafts + feedback
    # profile, applications (and their tasks), and remaining tasks cascade from User
    db.delete(user)
    db.commit()
