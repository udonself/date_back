from math import ceil
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from sqlalchemy import func

# from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, Category, CategoryOut
from helpers import get_user_by_token


categories_router = APIRouter(tags=['Categories'])
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/categories/add')


@categories_router.get("/categories/get", response_model=List[CategoryOut])
def get_categories(session = Depends(depends_db)):
    categories = session.query(Category).all()
    
    return categories




    
    