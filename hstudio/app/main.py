from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session

from hhutil.functools import find

from hstudio.app import crud, models, schemas
from hstudio.app.enums import TaskStatus
from hstudio.app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/workers/", response_model=schemas.Worker)
def create_worker(worker: schemas.WorkerCreate, db: Session = Depends(get_db)):
    return crud.create_worker(db=db, worker=worker)


@app.post("/workers", status_code=status.HTTP_201_CREATED)
def register(worker: schemas.WorkerCreate, response: Response, db: Session = Depends(get_db)):
    worker_name = worker.name
    db_worker = crud.get_worker_by_name(db, worker_name)
    if db_worker is not None:
        worker_tasks = crud.get_worker_tasks(db, db_worker.id, [TaskStatus.INIT, TaskStatus.RUNNING])
        n_tasks = len(worker_tasks)
        if n_tasks == 0:
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
            return HTTPException(status_code=400, detail="Worker %s has been registered and %d tasks are in queue." % (worker_name, n_tasks))
    workers[worker_id] = {
        "info": worker_info,
        "heartbeat": datetime_now(),
    }
    worker_task_queue[worker_id] = deque()
    return workers[worker_id]


@app.get("/workers/", response_model=List[schemas.Worker])
def get_workers(name: Optional[str] = None, db: Session = Depends(get_db)):
    if name is not None:
        worker = crud.get_worker_by_name(db, name)
        if worker is None:
            raise HTTPException(status_code=404, detail="Worker not found")
        return [worker]
    workers = crud.get_workers(db)
    return workers


@app.get("/worker/{worker_id}", response_model=schemas.Worker)
def get_worker(worker_id: int, db: Session = Depends(get_db)):
    db_worker = crud.get_worker(db, worker_id=worker_id)
    if db_worker is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    return db_worker


@app.post("/workers/{worker_id}/tasks/")
def create_task_for_worker(
    worker_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)
):
    if crud.get_task_by_name(db, task.name) is not None:
        raise HTTPException(status_code=400, detail="Task named %s already exists." % task.name)
    task_id = crud.create_worker_task(db=db, task=task, worker_id=worker_id)
    return {"task_id": task_id}


@app.get("/tasks/", response_model=List[schemas.Task])
def get_tasks(name: Optional[str] = None, db: Session = Depends(get_db)):
    if name is not None:
        task = crud.get_task_by_name(db, name)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return [task]
    tasks = crud.get_tasks(db)
    return tasks


@app.get("/workers/{worker_id}/tasks/", response_model=List[schemas.Task])
def get_worker_tasks(worker_id: int, db: Session = Depends(get_db)):
    tasks = crud.get_worker_tasks(db, worker_id=worker_id)
    return tasks


@app.get("/tasks/pull", status_code=status.HTTP_200_OK)
def pull_task(worker_id: int, response: Response, db: Session = Depends(get_db)):
    if crud.get_worker(db, worker_id) is None:
        return HTTPException(status_code=404, detail="Worker not found")

    task = crud.get_pending_task(db, worker_id)
    if task is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None

    return task


@app.get("/tasks/{task_id}/", response_model=schemas.Task)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/tasks/{task_id}/log")
def get_task_log(task_id: int, db: Session = Depends(get_db)):
    log = crud.get_task_log(db, task_id=task_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"log": log}


@app.put("/tasks/{task_id}/log")
def update_task_log(task_id: int, log_patch: schemas.LogPatch, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task_id = crud.update_task_log(db, task_id, log_patch.log)
    return {"task_id": task_id}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: schemas.TaskUpdate, response: Response, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    prev_status = task['status']
    task_status = task_update.status
    if prev_status == task_status:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None

    if task_status in [schemas.TaskStatus.SUCCESS, schemas.TaskStatus.ERROR]:
        worker_task_queue[worker_id].popleft()
    # TODO: Check other status change
    return None