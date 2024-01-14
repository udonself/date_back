from math import ceil

from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from sqlalchemy import func

# from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, Category, CategoryToAdd
from helpers import get_user_by_token


categories_router = APIRouter(tags=['Categories'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/categories/add')


@categories_router.get("/categories/get")
def get_categories(session = Depends(depends_db)):
    categories = session.query(Category).all()
    
    return categories

@categories_router.post("/categories/add")
def add_category(data: CategoryToAdd, token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    if user.role != 'admin':
        raise HTTPException(status_code=401, detail="Нет доступа к такому функционалу")
    category = Category(
        name=data.name,
        icon=data.icon
    )
    session.add(category)
    session.commit()
    return {'message': 'Категория добавлена!'}





    
    