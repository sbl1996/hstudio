from enum import Enum

class RuntimeType(str, Enum):
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"


class TaskStatus(str, Enum):
    INIT = 'init'
    RUNNING = 'running'
    # Finished
    SUCCESS = 'success'
    ERROR = 'error'
