from typing import List
import base64
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
import requests

from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, User, UserRegister, UserUpdate, Category, CategoryOfUser, Like, Dislike, UserInfo
from helpers import get_user_by_token


users_router = APIRouter(
    tags=['User'],
    prefix='/users'
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/update')

ADMIN_IDS = [1]


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
        ],
        'isAdmin': user.id in ADMIN_IDS
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
    
    
@users_router.post("/block/{user_id}", response_model=UserInfo)
def block_user(user_id: int, token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    admin = get_user_by_token(token, session)
    if admin.id not in ADMIN_IDS:
        raise HTTPException(status_code=401, detail="Нет доступа")
    
    user = session.query(User).filter(User.id == user_id).first()
    user.blocked = True
    session.commit()
    
    return user


@users_router.post("/unblock/{user_id}", response_model=UserInfo)
def block_user(user_id: int, token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    admin = get_user_by_token(token, session)
    if admin.id not in ADMIN_IDS:
        raise HTTPException(status_code=401, detail="Нет доступа")
    
    user = session.query(User).filter(User.id == user_id).first()
    user.blocked = False
    session.commit()
    
    return user


@users_router.get("/all", response_model=List[UserInfo])
def block_user(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    admin = get_user_by_token(token, session)
    if admin.id not in ADMIN_IDS:
        raise HTTPException(status_code=401, detail="Нет доступа")
    
    users = session.query(
        User
    ).all()
    
    print(users)
    
    return users
    

@users_router.get("/auth")
def user_auth(username: str, password: str, session: Session = Depends(depends_db)):
    existing_user = session.query(User).filter(User.username==username).first()
    if not existing_user:
        raise HTTPException(status_code=401, detail="Неправильный логин или пароль")
    if not check_password(password, existing_user.password):
        raise HTTPException(status_code=401, detail="Неправильный логин или пароль")
    token = encode_jwt(get_user_payload(existing_user))
    return {'token': token}


@users_router.get("/find")
def find_user(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    
    if user.blocked:
        raise HTTPException(status_code=404, detail="Sender or receiver not found")
    
    user_categories_subquery = (
        session.query(CategoryOfUser.categoryId)
        .filter(CategoryOfUser.userId == user.id)
        .subquery()
    )  
    
    matching_categories_subquery = (
        session.query(
            CategoryOfUser.userId,
            func.count(CategoryOfUser.categoryId).label('matching_categories')
        )
        .filter(CategoryOfUser.categoryId.in_(user_categories_subquery))
        .group_by(CategoryOfUser.userId)
        .subquery()
    )

    liked_disliked_user_ids = session.query(Like.receiver_id).filter(Like.sender_id == user.id).union(
        session.query(Dislike.receiver_id).filter(Dislike.sender_id == user.id)
    ).all()

    liked_disliked_by_user_ids = session.query(Like.sender_id).filter(Like.receiver_id == user.id).union(
        session.query(Dislike.sender_id).filter(Dislike.receiver_id == user.id)
    ).all()
    
    subquery = session.query(CategoryOfUser.userId).filter(
        CategoryOfUser.userId == User.id
    ).exists()
    unknown_user_ids = session.query(
        User.id
    ).filter(
        or_(
            User.avatar == 'https://telegra.ph/file/d06a5bd7749a4fcff76b0.png',
            User.age == None,
            User.firstName == None,
            User.description == None,
            User.blocked == True,
            ~subquery
        )
    ).all()

    # Объединить все исключаемые user_id
    excluded_user_ids = {id for (id,) in liked_disliked_user_ids + liked_disliked_by_user_ids + unknown_user_ids}
    
    potential_user = (
        session.query(User, matching_categories_subquery.c.matching_categories).options(joinedload(User.categories))
        .filter(User.id != user.id, User.id.notin_(excluded_user_ids))
        .outerjoin(matching_categories_subquery, User.id == matching_categories_subquery.c.userId)
        .order_by(matching_categories_subquery.c.matching_categories.desc().nullslast(), User.id)
        .first()
    )

    u, count = potential_user
    return {
        'id': u.id,
        'firstName': u.firstName,
        'age': u.age,
        'avatar': u.avatar,
        'description': u.description,
        'categories': u.categories
    }
    

@users_router.post("/like/{receiver_id}")
def like_user(receiver_id: int, token: str = Depends(oauth2_scheme), return_likes: bool = False, session: Session = Depends(depends_db)):
    try:
        sender = get_user_by_token(token, session)
        receiver = session.query(User).filter(User.id == receiver_id).first()
        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="Sender or receiver not found")

        like = Like(sender_id=sender.id, receiver_id=receiver.id, liked_at=datetime.now())
        session.add(like)
        session.commit()
        if return_likes:
            return get_interactions(token, session)
        return find_user(token, session)

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@users_router.post("/dislike/{receiver_id}")
def dislike_user(receiver_id: int, token: str = Depends(oauth2_scheme), return_likes: bool = False, session: Session = Depends(depends_db)):
    try:
        sender = get_user_by_token(token, session)
        receiver = session.query(User).filter(User.id == receiver_id).first()
        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="Sender or receiver not found")

        dislike = Dislike(sender_id=sender.id, receiver_id=receiver.id)
        session.add(dislike)
        session.commit()
        if return_likes:
            return get_interactions(token, session)
        return find_user(token, session)

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@users_router.get("/interactions")
def get_interactions(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    user = get_user_by_token(token, session)

    # Подзапрос для поиска пользователей, которые лайкнули текущего пользователя
    likes_subquery = (
        session.query(Like.sender_id)
        .filter(Like.receiver_id == user.id)
        .subquery()
    )

    # Подзапрос для поиска пользователей, которые текущий пользователь дизлайкнул
    dislikes_subquery = (
        session.query(Dislike.receiver_id)
        .filter(Dislike.sender_id == user.id)
        .subquery()
    )

    # Поиск совпадений (matches)
    matches = (
        session.query(User).options(joinedload(User.categories))
        .join(Like, Like.receiver_id == User.id)
        .filter(
            Like.sender_id == user.id,
            User.id.in_(likes_subquery),
            User.id.notin_(dislikes_subquery)
        )
        .all()
    )

    # Извлечь IDs пользователей, которые уже являются совпадениями
    match_ids = {user.id for user in matches}

    # Поиск пользователей, которые лайкнули текущего пользователя, но не были им дизлайкнуты и не являются совпадениями
    likes = (
        session.query(User)
        .filter(
            User.id.in_(likes_subquery),
            User.id.notin_(dislikes_subquery),
            User.id.notin_(match_ids)
        )
        .all()
    )

    # Формирование списка likes
    likes_list = [
        {
            'id': u.id,
            'firstName': u.firstName,
            'age': u.age,
            'avatar': u.avatar,
            'description': u.description,
            'categories': u.categories
        } for u in likes
    ]

    # Формирование списка matches
    matches_list = [
        {
            'id': u.id,
            'firstName': u.firstName,
            'age': u.age,
            'avatar': u.avatar,
            'description': u.description,
            'categories': u.categories
        } for u in matches
    ]

    return {
        'likes': likes_list,
        'matches': matches_list
    }


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
    user.description = data.description
    
    user.categories.clear()
    categories_to_add = session.query(Category).filter(Category.id.in_(data.categories)).all()
    user.categories.extend(categories_to_add)

    session.commit()
    
    return {'ok': True, 'token': encode_jwt(get_user_payload(user))}
    