from enum import Enum
from typing import Optional
from datetime import datetime, timedelta

from pydantic import BaseModel


class RuntimeType(str, Enum):
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"


class WorkerInfo(BaseModel):
    id: str
    runtime_type: RuntimeType
    session_start: Optional[datetime]
    session_duration: Optional[timedelta]


# Worker
## Info