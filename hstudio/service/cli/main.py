import os

import typer
from hhutil.io import fmt_path

from hstudio.service.client import Client


def get_host():
    host = os.getenv("HSTUDIO_HOST")
    if host is None:
        raise ValueError("Environment variable HSTUDIO_HOST not found.")
    return host


def get_client():
    client = Client(host=get_host())
    return client


app = typer.Typer(add_completion=False)
workers_app = typer.Typer()
app.add_typer(workers_app, name="workers")
tasks_app = typer.Typer()
app.add_typer(tasks_app, name="tasks")


@workers_app.command("list")
def list_workers():
    client = get_client()
    print()
    client.list_workers()
    print()


@tasks_app.command("list")
def list_tasks():
    client = get_client()
    print()
    client.list_tasks()
    print()


@tasks_app.command("submit")
def submit_task(
    task_id: str,
    script_file: str = typer.Argument(..., help="Path to script file"),
    worker_id: str = typer.Argument(..., help="Worker to submitted task")):
    client = get_client()
    client.submit_task(task_id, script_file, worker_id)


@tasks_app.command("sync_log")
def sync_task_log(
    task_id: str,
    log_file: str = typer.Argument(..., help="File path to save log")):
    client = get_client()
    log_file = fmt_path(log_file)
    if log_file.exists() and log_file.is_dir():
        log_file = f"{log_file}/{task_id}.log"
    client.sync_log(task_id, log_file)


@tasks_app.command("delete")
def delete_task(
    task_id: str, force: bool = True,
    show: bool = typer.Argument(False, help="Show deleted task")):
    client = get_client()
    task = client.delete_task(task_id, force)
    if show:
        print(task)


if __name__ == "__main__":
    app()