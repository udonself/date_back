from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, or_, and_, String, text

from db import depends_db, User, Message, MessageToSend, ConversationOut, MessageOut, ConversationInfo
from helpers import get_user_by_token


messages_router = APIRouter(tags=['Messages'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/messages/send')

    
@messages_router.post('/messages/send')
def send_message(message_data: MessageToSend, token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    new_message = Message(
        to_id = message_data.to_id,
        from_id = user.id,
        content = message_data.content
    )
    session.add(new_message)
    session.commit()
    return new_message


@messages_router.get('/messages/get', response_model=ConversationOut)
def get_messages(companion_id: int , token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    subq = session.query(
        Message,
        func.extract('hour', Message.created).label('hour'),
        func.extract('minute', Message.created).label('minute')
    ).filter(
        or_(
            and_(Message.from_id == companion_id, Message.to_id == user.id),
            and_(Message.from_id == user.id, Message.to_id == companion_id)
        )
    ).order_by(Message.created).subquery()

    result = session.query(
        func.cast(func.date(subq.c.created), String).label('date'),
        func.json_agg(
            func.json_build_object(
                'from_id', subq.c.from_id,
                'content', subq.c.content,
                'hour', subq.c.hour,
                'minute', subq.c.minute
            )
        ).label('message_array')
    ).select_from(subq).group_by(func.date(subq.c.created)).order_by('date').all()
    
    
    messages_grouped_by_date = {}
    
    for (date, messages) in result:
        messages_grouped_by_date[date] = [MessageOut(from_id=msg['from_id'], content=msg['content'], hour=msg['hour'], minute=msg['minute']) for msg in messages]
    
    conversation = ConversationOut(
        messages_grouped_by_date = messages_grouped_by_date
    )

    return conversation



@messages_router.get('/messages/conversations', response_model=List[ConversationInfo])
def get_conversations(token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    user_id = user.id
    
    result = session.execute(text(f"""SELECT
    u.id AS interlocutor_id,
    u.username AS interlocutor_username,
    u.avatar AS interlocutor_avatar,
    m.content AS last_message_content,
    TO_CHAR(m.created, 'HH24:MI') AS last_message_created
FROM
    users u
JOIN
    messages m ON (u.id = m.from_id OR u.id = m.to_id)
WHERE
    (m.from_id = {user_id} OR m.to_id = {user_id})
    AND m.created = (
        SELECT MAX(created)
        FROM messages
        WHERE (from_id = u.id AND to_id = {user_id}) OR (from_id = {user_id} AND to_id = u.id)
    )
    ORDER BY m.created DESC;"""))
    print(result)
    
    return [
        ConversationInfo(
            companion_id=c_id,
            companion_username=c_name,
            companion_avatar=c_ava,
            last_message=c_msg,
            last_date=c_date
        ) for c_id, c_name, c_ava, c_msg, c_date in result
    ]
    
    