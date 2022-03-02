from datetime import datetime

import requests
from pydantic import BaseModel

from hstudio.utils import format_datetime, parse_datetime, datetime_now

class Item(BaseModel):
    id: str
    desc: str
    created_at: datetime

item = Item(id="foo", desc="hello, ffff", created_at=datetime_now())
rep = requests.post("http://localhost:8000/items/asd", data=item.json())