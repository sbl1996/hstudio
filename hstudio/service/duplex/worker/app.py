import os

from fastapi import FastAPI

from hstudio.service.worker import WorkerInfo, detect_runtime, register
from hstudio.service.worker.colab import get_public_addr

app = FastAPI()
global_state = {}

@app.on_event("startup")
def startup_event():
    wid = os.getenv("HSTUDIO_WORKER_ID", 'hstudio-default-worker')
    port = int(os.getenv('HSTUDIO_WORKER_PORT', '8001'))
    addr = get_public_addr(port)
    info = WorkerInfo(
        id=wid, addr=addr, runtime_type=detect_runtime(),
        session_start=os.getenv("HSTUDIO_SESSION_START"),
        session_duration=os.getenv("HSTUDIO_SESSION_DURATION"),
    )
    host = os.getenv("HSTUDIO_HOST")
    assert host is not None
    info = register(info, host)
    global_state['info'] = info


@app.get("/")
def hello():
    return "hello"


@app.get("/heartbeat", status_code=200)
def heartbeat():
    return "Alive"


@app.get("/info", status_code=200)
def get_info():
    return global_state['info'].json()
