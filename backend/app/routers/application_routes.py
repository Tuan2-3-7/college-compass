from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user
from ..database import get_db
from ..models import Application, StudentProfile, Task, University, User
from ..schemas import ApplicationIn, ApplicationOut, ApplicationUpdate, TaskOut
from ..services.checklist import generate_tasks, resolve_deadline

router = APIRouter(prefix="/api/applications", tags=["applications"])


def _owned_application(db: Session, user: User, application_id: int) -> Application:
    app = (
        db.query(Application)
        .options(joinedload(Application.university))
        .filter(Application.id == application_id, Application.user_id == user.id)
        .first()
    )
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.get("", response_model=list[ApplicationOut])
def list_applications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Application)
        .options(joinedload(Application.university))
        .filter(Application.user_id == user.id)
        .order_by(Application.deadline.is_(None), Application.deadline)
        .all()
    )


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(
    data: ApplicationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    university = db.get(University, data.university_id)
    if university is None:
        raise HTTPException(status_code=404, detail="University not found")
    existing = (
        db.query(Application)
        .filter(Application.user_id == user.id, Application.university_id == data.university_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="This university is already on your list")

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if profile is None:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        db.flush()

    app = Application(
        user_id=user.id,
        university_id=university.id,
        round=data.round,
        deadline=resolve_deadline(university.deadlines or {}, data.round),
    )
    db.add(app)
    db.flush()

    # personalized checklist: student type + level + university + round
    for task_data in generate_tasks(profile, university, data.round):
        db.add(Task(user_id=user.id, application_id=app.id, **task_data))

    db.commit()
    db.refresh(app)
    return app


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: int,
    data: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = _owned_application(db, user, application_id)
    changes = data.model_dump(exclude_unset=True)

    round_changed = "round" in changes and changes["round"] != app.round
    for field, value in changes.items():
        setattr(app, field, value)

    if round_changed:
        # deadline follows the round; regenerate auto tasks that are still open
        app.deadline = resolve_deadline(app.university.deadlines or {}, app.round)
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        (
            db.query(Task)
            .filter(
                Task.application_id == app.id,
                Task.auto_generated.is_(True),
                Task.status != "done",
            )
            .delete()
        )
        done_titles = {
            t.title
            for t in db.query(Task).filter(Task.application_id == app.id, Task.status == "done")
        }
        for task_data in generate_tasks(profile, app.university, app.round):
            if task_data["title"] not in done_titles:
                db.add(Task(user_id=user.id, application_id=app.id, **task_data))

    db.commit()
    db.refresh(app)
    return app


@router.delete("/{application_id}", status_code=204)
def delete_application(
    application_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    app = _owned_application(db, user, application_id)
    db.delete(app)
    db.commit()


@router.get("/{application_id}/tasks", response_model=list[TaskOut])
def application_tasks(
    application_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    _owned_application(db, user, application_id)
    return (
        db.query(Task)
        .filter(Task.application_id == application_id, Task.user_id == user.id)
        .order_by(Task.sort_order)
        .all()
    )
