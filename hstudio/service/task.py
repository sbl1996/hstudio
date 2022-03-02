import sys
import subprocess
from datetime import datetime
from enum import Enum

from pydantic.main import BaseModel

from hhutil.io import fmt_path
from hstudio.service.common import HSTUDIO_HOME
from hstudio.utils import datetime_now, decode_script


class TaskInfo(BaseModel):
    id: str
    script: str
    worker_id: str
    created_at: datetime
    started_at: datetime = None
    finished_at: datetime = None
    is_success: bool = None


class TaskStatus(str, Enum):
    INIT = 'init'
    RUNNING = 'running'
    # Finished
    SUCCESS = 'success'
    ERROR = 'error'


class TaskInfoWithStatus(BaseModel):
    info: TaskInfo
    status: TaskStatus


class TaskLogPatch(BaseModel):
    content: str


class Task:

    def __init__(self, info: TaskInfo):
        self.info = info
        self.status = TaskStatus.INIT

        self.process = None

        self.work_dir = fmt_path(HSTUDIO_HOME) / self.info.id
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.script_file = self.work_dir / "train.py"
        self.script_file.write_text(decode_script(self.info.script))

        self.log_file = self.work_dir / "train.log"

    def get_log(self):
        return self.log_file.read_text()

    def check_status(self):
        if self.process is None:
            return TaskStatus.INIT
        ret = self.process.poll()
        if ret is None:
            return TaskStatus.RUNNING
        elif ret == 0:
            return TaskStatus.SUCCESS
        else:
            return TaskStatus.ERROR

    def start(self):
        python_bin = sys.executable
        self.process = subprocess.Popen(f"{python_bin} -u {self.script_file} > {self.log_file} 2>&1", shell=True)
        self.info.started_at = datetime_now()

    def after_finish(self):
        self.info.finished_at = datetime_now()

    def after_success(self):
        self.after_finish()
        self.info.is_success = True

    def after_error(self):
        self.after_finish()
        self.info.is_success = False