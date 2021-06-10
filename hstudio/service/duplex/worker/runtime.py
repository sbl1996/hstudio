import os
import subprocess
from enum import Enum

class RuntimeType(str, Enum):
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"

def is_tpu_avaliable():
    return os.getenv("COLAB_TPU_ADDR") is not None


def is_gpu_avaliable():
    result = subprocess.run("nvidia-smi", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def detect_runtime():
    if is_tpu_avaliable():
        return RuntimeType.TPU
    elif is_gpu_avaliable():
        return RuntimeType.GPU
    else:
        return RuntimeType.CPU