from math import ceil

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from sqlalchemy import func

# from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, Category


categories_router = APIRouter(tags=['Categories'])


@categories_router.get("/categories/get")
def get_categories(session = Depends(depends_db)):
    categories = session.query(Category).all()
    
    return categories





    
    