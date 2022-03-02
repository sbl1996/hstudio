from typing import Dict, Deque
from collections import deque

from fastapi import FastAPI, Response, status

from hstudio.service.task import TaskInfo, TaskStatus, TaskInfoWithStatus, TaskLogPatch
from hstudio.service.worker import WorkerInfo
from hstudio.utils import datetime_now

# TODO: OpenAPI URL now rewrited by nginx, use parameters directly
app = FastAPI()

tasks = {}
workers: Dict[str, Dict] = {}

worker_task_queue: Dict[str, Deque[str]] = {} # worker -> queue[task_id]


def text_response(detail):
    return {"detail": detail}


@app.get("/")
def hello():
    return {"hello": "world"}

### Client API

@app.get("/workers")
def get_workers():
    res = []
    for worker_id in workers:
        worker = {
            **workers[worker_id],
            "running_task": None,
        }
        queue = worker_task_queue[worker_id]
        if len(queue) != 0:
            task_id = queue[0]
            if tasks[task_id]['status'] == TaskStatus.RUNNING:
                worker['running_task'] = task_id
        res.append(worker)
    return res



@app.get("/tasks")
def get_tasks():
    return [{"info": task['info'], 'status': task['status']} for task in tasks.values()]


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def handle_submit_task(task: TaskInfo, response: Response):
    worker_id = task.worker_id
    if worker_id not in workers:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found worker %s" % worker_id)
    if task.id in tasks:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return text_response("task %s already exists" % task.id)
    tasks[task.id] = {
        "info": task,
        "status": TaskStatus.INIT,
        "log": None,
    }
    worker_task_queue[worker_id].append(task.id)
    return task


@app.delete("/tasks/{task_id}/force", status_code=status.HTTP_200_OK)
def handle_force_delete_task(task_id: str, response: Response):
    if task_id not in tasks:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found task %s" % task_id)

    task = tasks[task_id]
    del tasks[task_id]

    worker_id = task['info'].worker_id
    queue = worker_task_queue[worker_id]
    try:
        queue.remove(task_id)
    except ValueError:
        pass
    return task


@app.get("/tasks/{task_id}/log", status_code=status.HTTP_200_OK)
def get_task_log(task_id: str, response: Response):
    if task_id not in tasks:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found task %s" % task_id)
    task = tasks[task_id]
    return {
        "data": task['log'],
    }


def delete_worker(worker_id, workers, tasks, worker_task_queue):

    worker = workers[worker_id]
    del workers[worker_id]
    del worker_task_queue[worker_id]

    worker_tasks = []
    for task_id, task in tasks.items():
        if task.info.worker_id == worker_id:
            worker_tasks.append(task)

    for task in worker_tasks:
        del tasks[task.info.id]

    return worker, worker_tasks


@app.delete("/workers/{worker_id}", status_code=status.HTTP_200_OK)
def handle_delete_worker(worker_id: str, response: Response):

    if worker_id not in workers:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found worker %s" % worker_id)

    n_tasks = len(worker_task_queue[worker_id])
    if n_tasks == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return text_response("%d tasks are in queue, use force delete." % n_tasks)

    worker, worker_tasks = delete_worker(
        worker_id, workers, tasks, worker_task_queue)
    return {
        "worker": worker,
        "tasks": worker_tasks,
    }


@app.delete("/workers/{worker_id}/force", status_code=status.HTTP_200_OK)
def handle_force_delete_worker(worker_id: str, response: Response):

    if worker_id not in workers:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found worker %s" % worker_id)

    worker, worker_tasks = delete_worker(
        worker_id, workers, tasks, worker_task_queue)
    return {
        "worker": worker,
        "tasks": worker_tasks,
    }


### Worker API

@app.post("/workers", status_code=status.HTTP_201_CREATED)
def register(worker_info: WorkerInfo, response: Response):
    worker_id = worker_info.id
    if worker_id in workers:
        n_tasks = len(worker_task_queue[worker_id])
        if n_tasks == 0:
            prev_worker_info = workers[worker_id]
            workers[worker_id] = {
                "info": worker_info,
                "heartbeat": datetime_now(),
            }
            response.status_code = status.HTTP_200_OK
            return {
                **workers[worker_id],
                "prev": prev_worker_info,
            }
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return text_response("Worker %s has been registered and %d tasks are in queue." % (worker_id, n_tasks))
    workers[worker_id] = {
        "info": worker_info,
        "heartbeat": datetime_now(),
    }
    worker_task_queue[worker_id] = deque()
    return workers[worker_id]


@app.post("/workers/{worker_id}/heartbeat", status_code=status.HTTP_200_OK)
def heartbeat(worker_id: str, response: Response):
    if worker_id not in workers:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found worker %s" % worker_id)

    workers[worker_id]['heartbeat'] = datetime_now()
    return {"heartbeat": workers[worker_id]['heartbeat']}


@app.get("/tasks/{worker_id}/pull", status_code=status.HTTP_200_OK)
def handle_pull_task(worker_id: str, response: Response):
    if worker_id not in workers:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found worker %s" % worker_id)

    task_queue = worker_task_queue[worker_id]
    if len(task_queue) == 0:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None

    task_id = task_queue[0]
    task_info = tasks[task_id]['info']
    return task_info


@app.put("/tasks/{worker_id}/log", status_code=status.HTTP_200_OK)
def handle_task_sync_log(worker_id: str, task_log: TaskLogPatch, response: Response):
    if worker_id not in workers:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found worker %s" % worker_id)

    queue = worker_task_queue[worker_id]
    if len(queue) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("no task running on %d" % worker_id)
    task_id = queue[0]
    task = tasks[task_id]
    task['log'] = task_log.content
    return None


@app.put("/tasks/{worker_id}", status_code=status.HTTP_200_OK)
def handle_task_update(worker_id: str, task_info_with_status: TaskInfoWithStatus, response: Response):
    if worker_id not in workers:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found worker %s" % worker_id)

    task_info = task_info_with_status.info
    task_status = task_info_with_status.status
    task_id = task_info.id
    if task_id not in tasks:
        response.status_code = status.HTTP_404_NOT_FOUND
        return text_response("not found task %s" % task_id)

    prev_status = tasks[task_id]['status']
    if prev_status == task_status:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None

    tasks[task_id]['info'] = task_info
    tasks[task_id]['status'] = task_status
    if task_status in [TaskStatus.SUCCESS, TaskStatus.ERROR]:
        worker_task_queue[worker_id].popleft()
    # TODO: Check other status change
    return None