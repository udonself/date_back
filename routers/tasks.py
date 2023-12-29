from typing import List

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from sqlalchemy import func

from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, Task, TaskInfo, ResponseToTask, Category


tasks_router = APIRouter(tags=['Tasks'])


@tasks_router.get("/tasks/get", response_model = List[TaskInfo])
def user_auth(page: int = 1, page_size: int = 1, pattern = r'%', session = Depends(depends_db)):
    tasks = session.query(Task.id, Category.name, Task.title, func.count(ResponseToTask.id).label('responses'), Task.created).\
        select_from(Task).\
        filter(Task.title.ilike(f'%{pattern}%')).\
        join(ResponseToTask, Task.id == ResponseToTask.task_id, isouter=True).\
        join(Category, Task.category_id == Category.id).\
        group_by(Task.id, Category.name).\
        order_by(Task.created).\
        offset((page - 1) * page_size).limit(page_size)
    print(tasks)
    return [
        TaskInfo(id = id, category = category, title = title, responses = responses, created = created) 
            for (id, category, title, responses, created) in tasks
    ]





    
    