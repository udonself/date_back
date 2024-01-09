
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, or_, and_, String

from db import depends_db, User, Message, MessageToSend, ConversationOut, MessageOut
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