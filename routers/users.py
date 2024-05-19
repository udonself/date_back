import base64

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
import requests

from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, User, UserRegister, UserUpdate, Category, CategoryOfUser
from helpers import get_user_by_token


users_router = APIRouter(
    tags=['User'],
    prefix='/users'
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/update')


def get_user_payload(user: User) -> dict:
    
    return {
        'id': user.id,
        'username': user.username,
        'avatar': user.avatar,
        'firstName': user.firstName,
        'description': user.description,
        'age': user.age,
        'categories': [
            {'id': c.id, 'name': c.name} for c in user.categories
        ]
    }
    
    
@users_router.post("/register")
def user_register(user: UserRegister, session: Session = Depends(depends_db)):
    existing_user = session.query(User).filter(User.username==user.username).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
    new_user = User(
        username = user.username,
        password = hash_password(user.password),
    )
    session.add(new_user)
    session.commit()
    token = encode_jwt(get_user_payload(new_user))
    return {'token': token}


@users_router.get("/test")
def user_auth(session: Session = Depends(depends_db)):
    user_id = 1 
    user_with_categories = session.query(User).options(joinedload(User.categories)).filter(User.id == user_id).one()
    return user_with_categories
    
    # category = session.query(Category).filter(Category.id == 2).first()
    
    # user_with_categories.categories.append(category)
    
    # session.commit()
    
    # return {}
    


@users_router.get("/auth")
def user_auth(username: str, password: str, session: Session = Depends(depends_db)):
    existing_user = session.query(User).filter(User.username==username).first()
    if not existing_user:
        raise HTTPException(status_code=401, detail="Неправильный логин или пароль")
    if not check_password(password, existing_user.password):
        raise HTTPException(status_code=401, detail="Неправильный логин или пароль")
    token = encode_jwt(get_user_payload(existing_user))
    return {'token': token}


# @users_router.get('/me')
# def get_me(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
#     user = get_user_by_token(token, session)
    
#     return {'ok': True, 'token': encode_jwt(get_user_payload(user))}


@users_router.post("/update")
def update_info(data: UserUpdate, token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    
    if len(data.avatar) < 70:
        telegraph_url = data.avatar
    else:
        base64avatar = data.avatar
        response = requests.post('https://telegra.ph/upload', files = {"file": ('image.jpg', base64.b64decode(base64avatar), 'image/jpeg')})
        telegraph_url = 'https://telegra.ph' + response.json()[0]['src']
    
    # update user info
    user.age = data.age
    user.avatar = telegraph_url
    user.firstName = data.firstName
    session.commit()
    
    return {'ok': True, 'token': encode_jwt(get_user_payload(user))}
    