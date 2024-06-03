import json

from fastapi import HTTPException
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import joinedload
import requests

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


def notify_about_update(user: User, bot_token: str, manager_id: int | str):
    
    URL = f'https://api.telegram.org/bot{bot_token}/sendPhoto'

    keyboard = {
        "inline_keyboard": [
            [{"text": "❌Заблокировать" if not user.blocked else "✅Разблокировать", "callback_data": f"{'unblock' if user.blocked else 'block'} {user.id}"}],
            [{"text": "Пропустить", "callback_data": "skip"}]
        ]
    }
    text = f'{user.firstName}, {user.age}. {user.description}'

    # Формируем payload для HTTP-запроса
    payload = {
    'chat_id': manager_id,
    'photo': user.avatar,
    'caption': text,
    'reply_markup': json.dumps(keyboard)
    }

    # Отправка HTTP-запроса
    response = requests.post(URL, data=payload)