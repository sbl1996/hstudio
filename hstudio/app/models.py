from sqlalchemy import Column, ForeignKey, Integer, String, Enum, DateTime, Interval, Boolean, Text
from sqlalchemy.orm import relationship

from hstudio.app.database import Base
from hstudio.app.enums import RuntimeType, TaskStatus


def list_enum(enum_cls):
    return [e.value for e in enum_cls]


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    runtime_type = Column(Enum(*list_enum(RuntimeType), name="runtime_type"))
    session_start = Column(DateTime, nullable=True)
    session_duration = Column(Interval, nullable=True)

    tasks = relationship("Task", back_populates="worker")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    script = Column(Text)
    created_at = Column(DateTime)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(Enum(*list_enum(TaskStatus), name="status"))
    log = Column(Text)

    worker_id = Column(Integer, ForeignKey("workers.id"), index=True)
    worker = relationship("Worker", back_populates="tasks")
