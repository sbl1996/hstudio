from typing import List, Tuple

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from hstudio.app import models, schemas
from hstudio.app.enums import TaskStatus
from hstudio.utils import datetime_now


def get_worker(db: Session, worker_id: int):
    return db.query(models.Worker).filter(models.Worker.id == worker_id).first()


def get_worker_by_name(db: Session, name: str):
    return db.query(models.Worker).filter(models.Worker.name == name).first()


def get_workers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Worker).offset(skip).limit(limit).all()


def create_worker(db: Session, worker: schemas.WorkerCreate):
    db_worker = models.Worker(**worker.dict())
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return db_worker


def _task_columns():
    table = models.Task
    return table.id, table.name, table.script, table.created_at, \
           table.started_at, table.finished_at, table.status, table.worker_id


def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(*_task_columns()).offset(skip).limit(limit).all()


def get_worker_tasks(db: Session, worker_id: int, status=None):
    if status is None:
        status = []
    elif isinstance(status, TaskStatus):
        status = [status]
    filters = [models.Task.status == s for s in status]
    return db.query(*_task_columns()).filter(
            models.Task.worker_id == worker_id, *filters).all()


def get_pending_task(db: Session, worker_id: int):
    table = models.Task
    return db.query(*_task_columns())\
        .filter(table.worker_id == worker_id, table.status == TaskStatus.INIT)\
        .order_by(table.created_at.desc())\
        .first()


def get_task(db: Session, task_id: int):
    return db.query(*_task_columns()).filter(models.Task.id == task_id).first()


def get_task_by_name(db: Session, name: str):
    return db.query(*_task_columns()).filter(models.Task.name == name).first()


def get_task_log(db: Session, task_id: int):
    result = db.query(models.Task.log).filter(models.Task.id == task_id).first()
    if result is not None:
        result = result[0]
    return result


def create_worker_task(db: Session, task: schemas.TaskCreate, worker_id: int):
    created_at = datetime_now()
    db_task = models.Task(
        **task.dict(), created_at=created_at, status=TaskStatus.INIT, log="",
        worker_id=worker_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task.id


def update_task_log(db: Session, task_id: int, log: str):
    db_task = db.execute(
        select(models.Task).filter_by(id = task_id)).scalar_one()
    db_task.log = log
    db.commit()
    db.refresh(db_task)
    return db_task.id


def update_task(db: Session, task_id: int, task_update: schemas.TaskUpdate):
    db_task = db.execute(
        select(models.Task).filter_by(id = task_id)).scalar_one()
    if task_update.started_at is not None:
        db_task.started_at = task_update.started_at
    if task_update.finished_at is not None:
        db_task.finished_at = task_update.finished_at
    db_task.status = task_update.status
    db.commit()
    db.refresh(db_task)
    return db_task.id