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
    age = Column(Integer)
    avatar = Column(String, default='https://telegra.ph/file/d06a5bd7749a4fcff76b0.png')
    description = Column(String)
    blocked = Column(Boolean, default=False)
    categories = relationship('Category', secondary='categories_of_users', back_populates='users')
    

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    users = relationship('User', secondary='categories_of_users', back_populates='categories')
    
    
class CategoryOfUser(Base):
    __tablename__ = 'categories_of_users'
    
    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    categoryId = Column(Integer, ForeignKey(f'{Category.__tablename__}.id'))


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
    