from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, or_, and_, String, text

from db import depends_db, User, Message, MessageToSend, ConversationOut, MessageOut, ConversationInfo, ConversationOut, ConversationOutMessages
from helpers import get_user_by_token


messages_router = APIRouter(
    tags=['Messages'],
    prefix='/messages'
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/messages/send')

    
@messages_router.post('/send')
def send_message(message_data: MessageToSend, token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    new_message = Message(
        receiver_id = message_data.to_id,
        sender_id = user.id,
        message_text = message_data.content
    )
    session.add(new_message)
    session.commit()
    return get_messages(message_data.to_id, token, session)


@messages_router.get('/get', response_model=ConversationOut)
def get_messages(companion_id: int , token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    subq = session.query(
        Message,
        func.extract('hour', Message.sent_at).label('hour'),
        func.extract('minute', Message.sent_at).label('minute')
    ).filter(
        or_(
            and_(Message.sender_id == companion_id, Message.receiver_id == user.id),
            and_(Message.sender_id == user.id, Message.receiver_id == companion_id)
        )
    ).order_by(Message.sent_at).subquery()

    result = session.query(
        func.cast(func.date(subq.c.sent_at), String).label('date'),
        func.json_agg(
            func.json_build_object(
                'from_id', subq.c.sender_id,
                'content', subq.c.message_text,
                'hour', subq.c.hour,
                'minute', subq.c.minute
            )
        ).label('message_array')
    ).select_from(subq).group_by(func.date(subq.c.sent_at)).order_by('date').all()
    
    companion = session.query(
        User
    ).filter(
        User.id == companion_id
    ).first()
    
    
    messages_grouped_by_date = {}
    
    for (date, messages) in result:
        messages_grouped_by_date[date] = [MessageOut(from_id=msg['from_id'], content=msg['content'], hour=msg['hour'], minute=msg['minute']) for msg in messages]
    
    return ConversationOut(
        name=companion.firstName,
        avatar=companion.avatar,
        messages=ConversationOutMessages(
            messages_grouped_by_date = messages_grouped_by_date
        )
    )



@messages_router.get('/conversations', response_model=List[ConversationInfo])
def get_conversations(token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    user_id = user.id
    
    result = session.execute(text(f"""SELECT
        u.id AS interlocutor_id,
        u."firstName" AS interlocutor_username,
        u.avatar AS interlocutor_avatar,
        m.message_text AS last_message_content,
        TO_CHAR(m.sent_at, 'HH24:MI') AS last_message_created
    FROM
        users u
    JOIN
        messages m ON (u.id = m.sender_id OR u.id = m.receiver_id)
    WHERE
        (m.sender_id = {user_id} OR m.receiver_id = {user_id})
        AND m.sent_at = (
            SELECT MAX(sent_at)
            FROM messages
            WHERE (sender_id = u.id AND receiver_id = {user_id}) OR (sender_id = {user_id} AND receiver_id = u.id)
        )
        ORDER BY m.sent_at DESC;"""))
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
    
    