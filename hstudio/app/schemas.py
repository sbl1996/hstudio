from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from hstudio.app.enums import RuntimeType, TaskStatus


class TaskBase(BaseModel):
    name: str
    script: str


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    status: TaskStatus


class Task(TaskBase):
    id: int
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    status: TaskStatus
    log: str = ""

    worker_id: int

    class Config:
        orm_mode = True


class LogPatch(BaseModel):
    log: str


class WorkerBase(BaseModel):
    name: str
    runtime_type: RuntimeType
    session_start: Optional[datetime]
    session_duration: Optional[timedelta]


class WorkerCreate(WorkerBase):
    pass


class Worker(WorkerBase):
    id: int

    class Config:
        orm_mode = True
