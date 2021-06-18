# Quickstart

HStudio is a simple distributed workload manager like Slurm, but capable of running on restricted heterogeneous environments (like colab). This section runs through the API for common usage in HStudio.

## Install

1. Clone the HStudio repository.
```bash
git clone https://github.com/sbl1996/hstudio.git
cd hstudio
```

2. Install HStudio and its requirements.
```bash
pip install -v -e .
```

3. Test HStudio CLI.
```bash
$ hstudio --help
Usage: hstudio [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  tasks
  workers
```

## Host

HStudio uses a central server (host) to manage all data and resources. We must tell HStudio the host's address before using it.

```bash
# Linux or macOS
export HSTUDIO_HOST="X.XXX.XX.XX"

# Windows
set "HSTUDIO_HOST=X.XXX.XX.XX"
```

## Worker

Workers are remote servers with powerful compute devices (CPU/GPU/TPU) to execute tasks. You can check all workers registered in host like this.

```bash
$ hstudio workers list

ID            Runtime    Remaining    RunningTask    Status        Heartbeat
------------  ---------  -----------  -------------  ------------  --------------
colab-main-1  TPU        16:28:22     CIFAR10-test   CONNECTED     06-18 16:59:04
colab-main-2  TPU        16:28:22                    CONNECTED     06-18 16:59:00
colab-main-3  TPU                                    DISCONNECTED  06-18 10:20:09
```

Choose an idle worker whose Status is CONNECTED and RunningTask is empty. We will submit a new task to it with the worker's ID.

## Task

Tasks are python scripts to be executed. Let's first see how to submit a new task.

```bash
$ hstudio tasks submit --help
Usage: hstudio tasks submit [OPTIONS] SCRIPT_FILE TASK_ID WORKER_ID

Arguments:
  SCRIPT_FILE  Path to python script file  [required]
  TASK_ID      Task ID, must be unique  [required]
  WORKER_ID    Worker to submitted task  [required]

Options:
  --help  Show this message and exit.
```

We need to provide a python script file, a unique task ID, and the ID of a worker where the task will run. It is better to provide the ID of an idle worker (like the one we chose before) and the task will be executed on it immediately. If a busy worker (whose Status is CONNECTED and RunningTask is not empty) is chosen, the task will be pending first and executed after the completion of all tasks come before.

HStudio has some example tasks for testing under the directory `examples/tasks`. We will run `cifar10.py`, which trains a ResNet-110 on CIFAR-10 dataset with 20 epochs.

```bash
$ hstudio tasks submit cifar10.py CIFAR10-test-2 colab-main-2
Task CIFAR10-test-2 submitted to colab-main-2 successfully.
```

Note that the TASK_ID must be unique and you may need to choose a different one.

After submitting, we can check the status of the task.

```bash
$ hstudio tasks list

ID              Worker        Status    Started         Finished        Created
--------------  ------------  --------  --------------  --------------  --------------
CIFAR10-test-2  colab-main-2  RUNNING   06-18 17:08:12                  06-18 17:08:06
CIFAR10-test    colab-main-1  SUCCESS   06-18 16:59:06  06-18 17:04:56  06-18 16:58:47
```

Status may be INIT when the task is just submitted, because it will take a while for host to assign tasks.

If the task starts running, we can sync its output (log) from host.

```bash
$ hstudio tasks sync_log --help
Usage: hstudio tasks sync_log [OPTIONS] TASK_ID TARGET

Arguments:
  TASK_ID  [required]
  TARGET   Target directory to save log  [required]

Options:
  -f / -d  Save log to file or directory  [default: False]
  --help   Show this message and exit.

$ hstudio tasks sync_log CIFAR10-test-2 logs
```

This example task will be completed after around 6 minutes. At anytime, you can check whether the task is finished.

```bash
$ hstudio tasks list
ID              Worker        Status    Started         Finished        Created
--------------  ------------  --------  --------------  --------------  --------------
CIFAR10-test-2  colab-main-2  SUCCESS   06-18 16:16:07  06-18 16:21:35  06-18 16:16:05
CIFAR10-test    colab-main-1  SUCCESS   06-18 16:12:08  06-18 16:17:39  06-18 16:12:05
```

After task success, sync task log and open `CIFAR10-test-2.log`. We find that the final training accuracy is 90.15% and test accuracy is 88.42%. Obviously, more epochs are needed for better performance. Try it!

Finally, we can delete tasks by ID. Remember not to delete a RUNNING task, which may cause unpredictable errors in host.

```bash
$ hstudio tasks delete --help
Usage: hstudio tasks delete [OPTIONS] TASK_ID [SHOW]

Arguments:
  TASK_ID  [required]
  [SHOW]   Show deleted task  [default: False]

Options:
  --force / --no-force  [default: True]
  --help                Show this message and exit.

$ hstudio tasks delete CIFAR10-test-2

$ hstudio tasks list

ID            Worker        Status    Started         Finished        Created
------------  ------------  --------  --------------  --------------  --------------
CIFAR10-test  colab-main-1  SUCCESS   06-18 16:59:06  06-18 17:04:56  06-18 16:58:47
```