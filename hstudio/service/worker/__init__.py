import time
from typing import Optional
from datetime import datetime, timedelta

import requests
from pydantic import BaseModel

from hstudio.service.worker.runtime import RuntimeType, detect_runtime
from hstudio.service.common import HEARTBEAT_INTERVAL
from hstudio.utils import format_url, parse_datetime, format_datetime, datetime_now
from hstudio.service.task import Task, TaskStatus, TaskInfo, TaskInfoWithStatus, TaskLogPatch


def log_info(msg):
    print("%s %s" % (datetime_now(format=True), msg))


EVENT_LOOP_INTERVAL = HEARTBEAT_INTERVAL


class WorkerInfo(BaseModel):
    id: str
    runtime_type: RuntimeType
    session_start: Optional[datetime]
    session_duration: Optional[timedelta]


class Worker:

    def __init__(self, id, runtime_type='auto', session_start=None, session_duration=None):
        if runtime_type == 'auto':
            runtime_type = detect_runtime()
        self.info = WorkerInfo(
            id=id, runtime_type=runtime_type,
            session_start=session_start,
            session_duration=session_duration)

        self.host = None
        self.last_heartbeat = None

        self.running_task: Optional[Task] = None
        self.task_status: Optional[TaskStatus] = None

    def register(self, host):
        host = format_url(host)
        rep = requests.post(host + "/workers", data=self.info.json())
        if rep.status_code == 201:
            self.last_heartbeat = parse_datetime(rep.json()['heartbeat'])
            self.host = host
        elif rep.status_code == 200:
            print("Found previous registered worker: %s" % rep.json()['prev'])
            self.last_heartbeat = parse_datetime(rep.json()['heartbeat'])
            self.host = host
        else:
            raise ConnectionError("Failed to connect to host: %s" % host)

    def assert_registered(self):
        assert self.host is not None, "Register first."

    def heartbeat(self):
        self.assert_registered()
        try:
            rep = requests.post(f"{self.host}/workers/{self.info.id}/heartbeat")
            if rep.status_code == 200:
                self.last_heartbeat = parse_datetime(rep.json()['heartbeat'])
                return True
            else:
                print("Heartbeat fails: %s" % rep.text)
                return False
        except ConnectionError as e:
            print("Network error: %s" % e)
            return False

    def pull_task(self) -> Optional[Task]:
        self.assert_registered()
        try:
            rep = requests.get(f"{self.host}/tasks/{self.info.id}/pull")
            if rep.status_code == 200:
                info = TaskInfo(**rep.json())
                return Task(info)
            elif rep.status_code == 204:
                return None
            else:
                print("Pull error: %s" % rep.text)
                return None
        except ConnectionError as e:
            print("Network error: %s" % e)
            return None

    def report_task_update(self):
        self.assert_registered()
        data = TaskInfoWithStatus(
            info=self.running_task.info,
            status=self.task_status,
        )
        rep = requests.put(f"{self.host}/tasks/{self.info.id}", data=data.json())
        if rep.status_code >= 400:
            print("Task update error: %s" % rep.text)

    def sync_log(self):
        self.assert_registered()
        log = TaskLogPatch(content=self.running_task.get_log())
        try:
            rep = requests.put(f"{self.host}/tasks/{self.info.id}/log", data=log.json())
            if rep.status_code >= 400:
                print("Sync log error: %s" % rep.text)
        except ConnectionError as e:
            print("Network error: %s" % e)

    def run(self):
        disconnect_count = 0
        if self.task_status is None:
            self.task_status = TaskStatus.INIT
        while True:
            heartbeat_rep = self.heartbeat()

            if not heartbeat_rep:
                disconnect_count += 1
                log_info("Disconnected for %d times, the lastest is %s." % (
                    disconnect_count, format_datetime(self.last_heartbeat)))
            else:
                if disconnect_count > 0:
                    log_info("Reconnected after %d times" % disconnect_count)
                disconnect_count = 0

                # IDLE
                if self.running_task is None:
                    task = self.pull_task()
                    if task is not None:
                        self.running_task = task
                        task.start()
                        self.task_status = TaskStatus.RUNNING
                        self.report_task_update()
                        log_info("Start running task %s" % task.info.id)
                # RUNNING
                else:
                    prev_task_status = self.task_status
                    self.task_status = self.running_task.check_status()
                    if self.task_status == TaskStatus.RUNNING:
                        log_info("Running task %s, log synced" % self.running_task.info.id)
                        self.sync_log()
                    elif self.task_status == TaskStatus.SUCCESS:
                        if prev_task_status == TaskStatus.RUNNING:
                            self.sync_log()
                            self.running_task.after_success()
                            self.report_task_update()
                            task_info = self.running_task.info
                            log_info("Task %s finished successfully" % task_info.id)
                            self.running_task = None
                        else:
                            # TODO: unknown state
                            print("Unknown transition: %s to %s" % (prev_task_status, self.task_status))
                            self.running_task = None
                    elif self.task_status == TaskStatus.ERROR:
                        if prev_task_status == TaskStatus.RUNNING:
                            self.sync_log()
                            self.running_task.after_error()
                            self.report_task_update()
                            task_info = self.running_task.info
                            log_info("Task %s finished with error" % task_info.id)
                            self.running_task = None
                        else:
                            # TODO: unknown state
                            print("Unknown transition: %s to %s" % (prev_task_status, self.task_status))
                            self.running_task = None
                    elif self.task_status == TaskStatus.INIT:
                        # TODO: unknown state
                        print("Unknown transition: %s to %s" % (prev_task_status, self.task_status))

            time.sleep(EVENT_LOOP_INTERVAL)