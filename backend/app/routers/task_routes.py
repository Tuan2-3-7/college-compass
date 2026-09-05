from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Application, Task, User
from ..schemas import TaskIn, TaskOut, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Task)
        .filter(Task.user_id == user.id)
        .order_by(Task.due_date.is_(None), Task.due_date, Task.sort_order)
        .all()
    )


@router.post("", response_model=TaskOut, status_code=201)
def create_task(data: TaskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.application_id is not None:
        owned = (
            db.query(Application)
            .filter(Application.id == data.application_id, Application.user_id == user.id)
            .first()
        )
        if owned is None:
            raise HTTPException(status_code=404, detail="Application not found")
    task = Task(user_id=user.id, auto_generated=False, **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
