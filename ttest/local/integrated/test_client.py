from hstudio.service.client import Client

host = "1.117.72.139/XPJarvef6GxRdtdc"
client = Client(host)
client.list_workers()

script_file = "/Users/hrvvi/Code/Library/hstudio/tests/local/integrated/tasks/fake.py"
client.submit_task("fake-1", script_file, worker_id='colab-main-1')

client.list_tasks()

script_file = "/Users/hrvvi/Code/Library/hstudio/tests/local/integrated/tasks/cifar100.py"
client.submit_task("test-cifar-1", script_file, worker_id='colab-main-1')
client.submit_task("test-cifar-1-3", script_file, worker_id='colab-main-3')

script_file = "/Users/hrvvi/Code/Library/hstudio/tests/local/integrated/tasks/cifar100_2.py"
client.submit_task("test-cifar-2", script_file, worker_id='colab-main-1')
client.submit_task("test-cifar-2-3", script_file, worker_id='colab-main-3')

script_file = "/Users/hrvvi/Code/Library/experiments/CIFAR100-TensorFlow/code/94.py"
client.submit_task("CIFAR100-TensorFlow-94-1", script_file, worker_id='colab-main-1')
client.submit_task("CIFAR100-TensorFlow-94-2", script_file, worker_id='colab-main-2')

script_file = "/Users/hrvvi/Code/Library/experiments/CIFAR100-TensorFlow/code/96.py"
client.submit_task("CIFAR100-TensorFlow-96-1", script_file, worker_id='colab-main-1')
client.submit_task("CIFAR100-TensorFlow-96-2", script_file, worker_id='colab-main-2')