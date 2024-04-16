from datetime import datetime

from sqlalchemy import Column, Float, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    firstName = Column(String)
    lastName = Column(String)
    city = Column(String)
    age = Column(Integer)
    isMale = Column(Boolean)
    avatar = Column(String)
    photos = relationship('Photo', backref='user')


class Photo(Base):
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    photo_url = Column(String)


class Like(Base):
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    receiver_id = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    liked_at = Column(DateTime, default=datetime.now)


class Dislike(Base):
    __tablename__ = 'dislikes'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    receiver_id = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))


class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    user2_id = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    matched_at = Column(DateTime, default=datetime.now)


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey(f'{Match.__tablename__}.id'))
    sender_id = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    receiver_id = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    message_text = Column(String)
    sent_at = Column(DateTime, default=datetime.now)
    