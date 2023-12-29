from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, UserRegister, UserOut, User


users_router = APIRouter(tags=['User'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/me')


@users_router.post("/users/register")
def user_register(user: UserRegister, session = Depends(depends_db)):
    existing_user = session.query(User).filter(User.username==user.username).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
    new_user = User(
        username = user.username,
        hashed_password = hash_password(user.password),
        role = user.role
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
    return {'token': token}


@users_router.get("/users/me", response_model=UserOut)
def user_info(token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Для выполнения этого запроса вам нужно авторизоваться")
    user_id = payload['id']
    user = session.query(User).filter(User.id == user_id).first()
    return user
    
    
    