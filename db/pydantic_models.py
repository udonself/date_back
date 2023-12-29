from datetime import datetime
from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str
    role: str
    
    
class UserOut(BaseModel):
    username: str
    role: str
    about: str | None
    avatar: str
    verified: bool
    balance: float
    
    
class TaskInfo(BaseModel):
    id: int
    category: str
    title: str
    responses: int
    created: datetime