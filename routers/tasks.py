from typing import List
from math import ceil

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func

from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, Task, TaskInfo, TasksOut, Category, TaskToCreate
from helpers import get_user_by_token


tasks_router = APIRouter(tags=['Tasks'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/tasks/create')


@tasks_router.get('/tasks/get', response_model = TasksOut)
def user_auth(page: int = 1, page_size: int = 1, pattern = r'%', session = Depends(depends_db)):
    query = session.query(Task.id, Category.name, Task.title, Task.created).\
        select_from(Task).\
        filter(Task.title.ilike(f'%{pattern}%')).\
        join(Category, Task.category_id == Category.id).\
        group_by(Task.id, Category.name).\
        order_by(Task.created.desc())

    total_tasks = query.count()
    total_pages = ceil(total_tasks / page_size)

    tasks = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return TasksOut(
        tasks=[TaskInfo(id=id, category=category, title=title, created=created)
            for (id, category, title, created) in tasks],
        total_pages=total_pages
    )

@tasks_router.post('/tasks/create')
def create_task(task_data: TaskToCreate, token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    new_task = Task(
        customer_id = user.id,
        category_id = task_data.category_id,
        title = task_data.title,
        description = task_data.description
    )
    session.add(new_task)
    session.commit()
    return new_task





    
    