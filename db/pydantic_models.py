from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel


class Category(BaseModel):
    id: int
    name: str
    

class UserRegister(BaseModel):
    username: str
    password: str
    role: str
    categories: List[Category] | None
    
    
class UserOut(BaseModel):
    id: int
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
    created: datetime


class TasksOut(BaseModel):
    tasks: List[TaskInfo]
    total_pages: int


class TaskOut(BaseModel):
    title: str
    description: str
    created: str
    customer_id: int
    customer_username: str
    customer_avatar: str
    caregory_name: str
    


class TaskToCreate(BaseModel):
    title: str
    description: str
    category_id: int


class FreelancerInfo(BaseModel):
    id: int
    username: str
    avatar: str
    verified: bool
    rating: float | None
    categories: List[str]


class FreelancersOut(BaseModel):
    freelancers: List[FreelancerInfo]
    total_pages: int



# models for user's profile 

class UserCategory(BaseModel):
    icon: str
    name: str


class UserReview(BaseModel):
    from_id: int
    from_avatar: str
    from_username: str
    date: str
    rating: int
    content: str


class ProfileOut(BaseModel):
    id: int
    role: str
    username: str
    avatar: str
    avg_rating: float | None
    user_categories: List[UserCategory]
    user_reviews: List[UserReview]


class UsernameToChange(BaseModel):
    new_username: str


class AvatarToChange(BaseModel):
    base64avatar: str
    
    
# review

class ReviewToCreate(BaseModel):
    to_id: int
    rating: int
    content: str


# messages

class MessageToSend(BaseModel):
    to_id: int
    content: str
    

class MessageOut(BaseModel):
    from_id: int
    content: str
    hour: int
    minute: int


class ConversationOut(BaseModel):
    messages_grouped_by_date: Dict[str, List[MessageOut]]

    
# conversations all

class ConversationInfo(BaseModel):
    companion_id: int
    companion_username: str
    companion_avatar: str
    last_message: str
    last_date: str


class UserToVerify(BaseModel):
    username: str


class CategoryToAdd(BaseModel):
    name: str
    icon: str
    


    