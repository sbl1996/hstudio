# Quickstart

## Install
Make sure you are in the root directory of `hstudio` (which has `setup.py`). Then run  `pip install -e .` and all completes.

## Use CLI
After install, run `python cli/main.py` to see avaliable commands.

Before running these commands, you should set enviroment variable `HSTUDIO_HOST` first.

Then run `python cli/main.py workers list` to see all workers. Select a CONNECTED worker and remenber its ID, we will submit a task to it.

Run `python cli/main.py tasks submit --help` and we find that TASK_ID, SCRIPT_FILE and WORKER_ID are required for submitting.

Let's start!

Run `python cli/main.py tasks submit TASK_ID examples/tasks/cifar100.py WORKER_ID` to submit an example task. Note that TASK_ID must be unique.

Run `python cli/main.py tasks list` to check whether our task is started.

If the task starts, run `python cli/main.py tasks sync_log TASK_ID LOG_DIR` to sync task log from host. Then check `LOG_DIR/TASK_ID.log` for task log.

At anytime, you can run `python cli/main.py tasks list` to check whether task task is finished.

You can also use `python cli/main.py tasks delete TASK_ID` to delete a task. But remenber not to delete a RUNNING task, which may cause state errors in host.