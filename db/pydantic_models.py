from typing import List
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


class TasksOut(BaseModel):
    tasks: List[TaskInfo]
    total_pages: int


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
    
    


    