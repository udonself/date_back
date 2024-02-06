from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    name: str
    imageUrl: str

    