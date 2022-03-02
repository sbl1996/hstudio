from hstudio.service.worker import Worker
from hstudio.utils import datetime_now

worker = Worker(id="local-1", runtime_type="cpu", session_start=datetime_now())


host = "http://1.117.72.139/XPJarvef6GxRdtdc"
worker.register(host)