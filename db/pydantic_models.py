from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    age: int | None
    avatar: str | None
    firstName: str | None
    description: str | None
    categories: list | None
    
    

    