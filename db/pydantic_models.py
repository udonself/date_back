from typing import List

from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    age: int
    avatar: str
    firstName: str
    description: str
    categories: List[int]
    
    

    