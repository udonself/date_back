from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    city: str
    age: int
    isMale: bool
    avatar: str
    firstName: str
    lastName: str
    
    

    