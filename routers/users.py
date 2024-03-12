import os
from typing import List
from math import ceil
import base64

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, JSON, literal
from sqlalchemy.orm import aliased, Session
import requests

from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, User, UserRegister
from helpers import get_user_by_token, getAmountOfCartItem


users_router = APIRouter(tags=['User'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/me')


@users_router.get("/users/isadmin")
def user_auth(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    return {
        'admin': str(user.id) in os.getenv('ADMIN_ID_LIST').split(",")
    }
    


@users_router.post("/users/register")
def user_register(user: UserRegister, session = Depends(depends_db)):
    existing_user = session.query(User).filter(User.username==user.username).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
    new_user = User(
        username = user.username,
        hashed_password = hash_password(user.password),
    )
    session.add(new_user)
    session.commit()
    token = encode_jwt({'id': new_user.id})
    return {'token': token}


@users_router.get("/users/auth")
def user_auth(username: str, password: str, session = Depends(depends_db)):
    existing_user = session.query(User).filter(User.username==username).first()
    if not existing_user:
        raise HTTPException(status_code=401, detail="Неправильный логин или пароль")
    if not check_password(password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="Неправильный логин или пароль")
    token = encode_jwt({'id': existing_user.id})
    return {'token': token, 'total_items': getAmountOfCartItem(existing_user, session)}


# @users_router.get("/users/me")
# def user_info(token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
#     return get_user_by_token(token, session)
