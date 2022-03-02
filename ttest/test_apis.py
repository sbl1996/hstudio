import requests

worker = {
    "name": "local-1",
    "runtime_type": "cpu",
}

task = {
    "name": "cifar-2",
    "script": r"""print("hello")""",
}

req = requests.post("http://localhost:8000/workers", json=worker)
print(req.json())
req = requests.post("http://localhost:8000/workers/1/tasks", json=task)
print(req.json())

data = {
    "content": "Epoch 1/2"
}
req = requests.put("http://localhost:8000/tasks/1/log", json=data)
req.json()