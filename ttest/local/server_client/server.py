from datetime import datetime

from fastapi import FastAPI, Response, status
from pydantic import BaseModel

class Item(BaseModel):
    id: str
    desc: str
    created_at: datetime

app = FastAPI()

@app.post("/items/{item_id}")
def create_foo(item_id: str, item: Item):
    print(item_id)
    print(item)
    return item