from typing import List
from math import ceil

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, JSON, literal
from sqlalchemy.orm import aliased

from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, UserRegister, UserOut, User, FreelancersCategory, Review, FreelancersOut, FreelancerInfo, Category, ProfileOut, UserCategory, UserReview


users_router = APIRouter(tags=['User'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/me')


@users_router.post("/users/register")
def user_register(user: UserRegister, session = Depends(depends_db)):
    print(user.categories)
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
    session.refresh(new_user)
    if new_user.role == 'freelancer':
        for category in user.categories:
            users_category = FreelancersCategory(
                freelancer_id = new_user.id,
                category_id = category.id
            )
            session.add(users_category)
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


@users_router.get("/users/freelancers/get", response_model = FreelancersOut)
def get_freelancers(page: int = 1, page_size: int = 10, session = Depends(depends_db)):
    query = session.query(User.id, User.username, User.avatar, User.verified, func.avg(Review.rating).label('rating'), func.array_agg(Category.name.distinct())).\
        select_from(User).\
        filter(User.role == 'freelancer').\
        join(FreelancersCategory, User.id == FreelancersCategory.freelancer_id, isouter=True).\
        join(Category, FreelancersCategory.category_id == Category.id, isouter=True).\
        join(Review, User.id == Review.to_id, isouter=True).\
        group_by(User.id)

    total_freelancers = query.count()
    total_pages = ceil(total_freelancers / page_size)

    freelancers = query.offset((page - 1) * page_size).limit(page_size).all()
    print(freelancers)
    return FreelancersOut(
        freelancers=[FreelancerInfo(id = id, username = username, avatar = avatar, verified = verified, rating = rating, categories=categories) 
            for (id, username, avatar, verified, rating, categories) in freelancers],
        total_pages=total_pages
    )


@users_router.get("/users/{user_id}", response_model = ProfileOut)
def get_user(user_id: int, session = Depends(depends_db)):
    users = aliased(User)
    reviews = aliased(Review)
    categories_of_freelancers = aliased(FreelancersCategory)
    categories = aliased(Category)

    subquery = (
        session.query(
            func.coalesce(
                func.json_agg(
                    func.json_build_object(
                        'icon', categories.icon,
                        'name', categories.name
                    )
                ).filter(
                    categories.icon.isnot(None),
                    categories.name.isnot(None)
                ),
                '[]'
            )
        )
        .select_from(categories_of_freelancers)
        .join(categories, categories_of_freelancers.category_id == categories.id)
        .filter(categories_of_freelancers.freelancer_id == users.id)
        .scalar_subquery()
    )

    avatar_subquery = (
        session.query(
            users.avatar,
            users.username,
            users.id
        ).group_by(users.id)
    ).subquery()  # Перенесите subquery() после закрытия скобки

    query = (
        session.query(
            users.id.label('id'),
            users.role.label('role'),
            users.username.label('username'),
            users.avatar.label('avatar'),
            func.avg(reviews.rating).label('avg_rating'),
            subquery.label('user_categories'),
            func.coalesce(
                func.json_agg(
                    func.json_build_object(
                        'from_id', reviews.from_id,
                        'from_avatar', avatar_subquery.c.avatar,  # Используйте avatar_subquery.c.avatar для получения значения
                        'from_username', avatar_subquery.c.username,
                        'date', func.date(reviews.created),
                        'rating', reviews.rating,
                        'content', reviews.content
                    )
                ).filter(reviews.from_id.isnot(None), avatar_subquery.c.id == reviews.from_id),
                '[]'
            ).label('user_reviews')
        )
        .outerjoin(reviews, users.id == reviews.to_id)
        .filter(users.id == user_id)
        .group_by(users.id)
    )

    result = query.first()
    (cid, role, username, avatar, avg_rating, user_categories, user_reviews) = result

    profile_info = ProfileOut(
        id=cid,
        role=role,
        username=username,
        avatar=avatar,
        avg_rating=avg_rating,
        user_categories=[UserCategory(icon=c['icon'], name=c['name']) for c in user_categories],
        user_reviews=[UserReview(from_id=r['from_id'], from_avatar=r['from_avatar'], from_username=r['from_username'], date=r['date'], rating=r['rating'], content=r['content']) for r in user_reviews],
    )

    return profile_info
