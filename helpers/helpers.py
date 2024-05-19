from fastapi import HTTPException
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import joinedload

from db import User
from security import decode_jwt


def get_user_by_token(token: str, session: Session) -> User:
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Для выполнения этого запроса вам нужно авторизоваться")
    user_id = payload['id']
    user = session.query(User).options(joinedload(User.categories)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Для выполнения этого запроса вам нужно авторизоваться")
    return user