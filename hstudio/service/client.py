from datetime import timedelta
from functools import cmp_to_key

import requests
from tabulate import tabulate

from hhutil.io import fmt_path

from hstudio.utils import format_url, datetime_now, parse_datetime, format_datetime, encode_script
from hstudio.service.common import DISCONNECTED_THRESHOLD
from hstudio.models.worker import WorkerInfo
from hstudio.service.task import TaskInfo, TaskStatus


def get_remaining(session_start, session_duration):
    now = datetime_now()
    elapsed = now - session_start
    remaining = session_duration - elapsed
    remaining = timedelta(seconds=remaining.seconds)
    return str(remaining)


CONNECTED = "CONNECTED"
DISCONNECTED = 'DISCONNECTED'


class Client:

    def __init__(self, host):
        host = format_url(host)
        rep = requests.get(host)
        if rep.status_code == 200:
            self.host = host
        else:
            raise ConnectionError("Failed to connect to host: %s" % host)

    # Host API

    def get_workers(self):
        workers = requests.get(self.host + "/workers").json()
        res = []
        for worker in workers:
            info = WorkerInfo(**worker['info'])
            res.append({
                'heartbeat': parse_datetime(worker['heartbeat']),
                'info': info,
                'running_task': worker['running_task'],
            })
        return res

    def get_tasks(self):
        tasks = requests.get(self.host + "/tasks").json()
        res = []
        for task in tasks:
            res.append({
                'info': TaskInfo(**task['info']),
                'status': task['status'],
            })
        return res

    def get_task_log(self, task_id):
        rep = requests.get(f"{self.host}/tasks/{task_id}/log")
        if rep.status_code == 200:
            return rep.json()['data']
        else:
            print("Error when getting task log: %s" % rep.text)

    def delete_task(self, task_id: str, force: bool):
        if force:
            rep = requests.delete(f"{self.host}/tasks/{task_id}/force")
            if rep.status_code == 200:
                return rep.json()
            else:
                ValueError("Error when deleting task: %s" % rep.text)
        else:
            raise NotImplementedError("Delete task without force")

    # Local

    def list_tasks(self):
        def fmt_datetime(dt):
            if dt is None:
                return None
            return dt.strftime("%m-%d %H:%M:%S")

        tasks = self.get_tasks()
        tasks = sort_task_for_show(tasks)
        rows = []
        for task in tasks:
            info = task['info']
            status = task['status']

            status = status.upper()
            started = fmt_datetime(info.started_at)
            finished = fmt_datetime(info.finished_at)
            created = fmt_datetime(info.created_at)
            rows.append([
                info.id, info.worker_id, status, started, finished, created])

        headers = ["ID", "Worker", "Status", "Started", "Finished", "Created"]
        print(tabulate(rows, headers=headers))


    def list_workers(self):
        def fmt_datetime(dt):
            if dt is None:
                return None
            return dt.strftime("%m-%d %H:%M:%S")

        workers = self.get_workers()
        now = datetime_now()
        rows = []
        for worker in workers:
            info = worker['info']
            last_heartbeat = worker['heartbeat']
            running_task = worker['running_task']

            runtime = info.runtime_type.upper()

            status = CONNECTED
            if (now - last_heartbeat).seconds > DISCONNECTED_THRESHOLD:
                status = DISCONNECTED

            remaining = None
            if info.session_start is not None and info.session_duration is not None and status != DISCONNECTED:
                remaining = get_remaining(info.session_start, info.session_duration)

            heartbeat = fmt_datetime(last_heartbeat)
            rows.append([info.id, runtime, remaining, running_task, status, heartbeat])

        headers = ["ID", "Runtime", "Remaining", "RunningTask", "Status", "Heartbeat"]
        print(tabulate(rows, headers=headers))

    def submit_task(self, id, script_file, worker_id):
        script_file = fmt_path(script_file)
        script = encode_script(script_file.read_text())
        task = TaskInfo(id=id, script=script, worker_id=worker_id, created_at=datetime_now())
        rep = requests.post(self.host + "/tasks", data=task.json())
        if rep.status_code == 201:
            print("Task %s submitted to %s successfully." % (id, worker_id))
        else:
            print("Task %s submit error: %s" % (id, rep.text))

    def sync_log(self, task_id, log_file):
        log = self.get_task_log(task_id)
        if log is None:
            print("No log from task %s" % task_id)
            return
        fmt_path(log_file).write_text(log)

status2int = {
    status: i
    for i, status in enumerate([
        TaskStatus.RUNNING, TaskStatus.INIT, TaskStatus.SUCCESS, TaskStatus.ERROR])
}

def sort_task_for_show(tasks):
    def cmp(task1, task2):
        d = status2int[task1['status']] - status2int[task2['status']]
        if d == 0:
            started1 = task1['info'].started_at
            started2 = task2['info'].started_at
            if started1 is not None and started2 is not None:
                return -(started1 - started2).total_seconds()
            else:
                created1 = task1['info'].created_at
                created2 = task2['info'].created_at
                return -(created1 - created2).total_seconds()
        return d
    return sorted(tasks, key=cmp_to_key(cmp))
