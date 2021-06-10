import os
import subprocess
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum

import requests
from pydantic import BaseModel

from hstudio.service.worker.runtime import RuntimeType
from hstudio.utils import format_url


class WorkerStatus(str, Enum):
    DISCONNECTED = 'disconnected'
    CONNECTED = "connected"


def register(worker_info, host):
    host = format_url(host)
    rep = requests.post(host + "/workers", data=worker_info.json())
    if rep.status_code == 200:
        return worker_info.copy(update={'host': host})
    else:
        raise ConnectionError("Failed to connect to host: %s" % host)


class WorkerInfo(BaseModel):
    id: str
    addr: str
    runtime_type: RuntimeType
    session_start: Optional[datetime]
    session_duration: Optional[timedelta]
    host: Optional[str]
