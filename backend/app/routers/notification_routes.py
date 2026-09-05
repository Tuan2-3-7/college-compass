from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Notification, Task, User
from ..services.readiness import readiness as readiness_service

router = APIRouter(prefix="/api", tags=["notifications"])


def _sync_notifications(db: Session, user: User) -> None:
    """Generate deadline notifications idempotently (dedupe_key prevents repeats)."""
    today = date.today()
    soon = today + timedelta(days=7)
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user.id, Task.status != "done", Task.due_date.isnot(None))
        .all()
    )
    existing = {
        n.dedupe_key
        for n in db.query(Notification).filter(Notification.user_id == user.id).all()
    }
    for task in tasks:
        if task.due_date < today:
            key = f"task-overdue-{task.id}"
            if key not in existing:
                db.add(Notification(
                    user_id=user.id, dedupe_key=key, category="overdue",
                    title=f"Overdue: {task.title}",
                    body=f"This task was due {task.due_date.isoformat()}.",
                    link="/applications",
                ))
        elif task.due_date <= soon:
            key = f"task-due-{task.id}-{task.due_date.isoformat()}"
            if key not in existing:
                db.add(Notification(
                    user_id=user.id, dedupe_key=key, category="deadline",
                    title=f"Due soon: {task.title}",
                    body=f"Due {task.due_date.isoformat()}.",
                    link="/applications",
                ))
    db.commit()


@router.get("/notifications")
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _sync_notifications(db, user)
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.read, Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "unread": sum(1 for n in notifications if not n.read),
        "notifications": [
            {
                "id": n.id, "category": n.category, "title": n.title, "body": n.body,
                "link": n.link, "read": n.read, "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
    }


@router.post("/notifications/{notification_id}/read")
def mark_read(
    notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    n = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if n is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = True
    db.commit()
    return {"ok": True}


@router.post("/notifications/read-all")
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.read.is_(False)
    ).update({"read": True})
    db.commit()
    return {"ok": True}


@router.get("/readiness")
def get_readiness(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return readiness_service(db, user)
