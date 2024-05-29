from typing import List, Dict

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


class MessageToSend(BaseModel):
    to_id: int
    content: str
    

class MessageOut(BaseModel):
    from_id: int
    content: str
    hour: int
    minute: int


class ConversationOutMessages(BaseModel):
    messages_grouped_by_date: Dict[str, List[MessageOut]]


class ConversationOut(BaseModel):
    name: str
    avatar: str
    messages: ConversationOutMessages


class ConversationInfo(BaseModel):
    companion_id: int | None
    companion_username: str | None
    companion_avatar: str | None
    last_message: str | None
    last_date: str | None
    
    
class UserInfo(BaseModel):
    id: int
    username: str | None
    avatar: str
    age: int | None
    description: str | None
    firstName: str | None
    blocked: bool
    
    

    