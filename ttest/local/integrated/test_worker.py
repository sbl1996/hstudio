from hstudio.service.worker import Worker
from datetime import timedelta
from hhutil.io import read_text

session_start = read_text("session_start.txt")
worker = Worker(id="colab-main-1", runtime_type="tpu",
                session_start=session_start[0], session_duration=timedelta(hours=24))

host = "http://1.117.72.139/XPJarvef6GxRdtdc"
worker.register(host)
