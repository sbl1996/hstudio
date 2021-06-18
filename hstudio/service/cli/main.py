import os
from pathlib import Path

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
    script_file: str = typer.Argument(..., help="Path to python script file"),
    task_id: str = typer.Argument(..., help="Task ID, must be unique"),
    worker_id: str = typer.Argument(..., help="Worker to submitted task")):
    client = get_client()
    client.submit_task(task_id, script_file, worker_id)


@tasks_app.command("sync_log")
def sync_task_log(
    task_id: str,
    target: Path = typer.Argument(..., help="Target directory to save log"),
    tofile: bool = typer.Option(False, "-f/-d", help="Save log to file or directory"),
):
    client = get_client()
    if tofile:
        log_file = fmt_path(target)
    else:
        target_dir = fmt_path(target)
        if target_dir.exists():
            assert target_dir.is_dir(), "Use --tofile to save log to file directly"
        else:
            target_dir.mkdir(parents=True)
        log_file = f"{target_dir}/{task_id}.log"
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