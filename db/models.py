from datetime import datetime

from sqlalchemy import Column, Float, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(70), unique=True)
    hashed_password = Column(String(100))
    
    
class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    imageUrl = Column(String(70))


class Brand(Base):
    __tablename__ = 'brands'
    id = Column(Integer, primary_key=True)
    name = Column(String(30))


class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    imageUrl = Column(String(70))
    price = Column(Float)
    description = Column(String(300))
    categoryId = Column(Integer, ForeignKey(f'{Category.__tablename__}.id'))
    brandId = Column(Integer, ForeignKey(f'{Brand.__tablename__}.id'))
    

class Cart(Base):
    __tablename__ = 'carts'
    
    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey(f'{User.__tablename__}.id'))
    active = Column(Boolean)


class ProductOfCart(Base):
    __tablename__ = 'products_of_carts'
    
    id = Column(Integer, primary_key=True)
    cartId = Column(Integer, ForeignKey(f'{Cart.__tablename__}.id'))
    productId = Column(Integer, ForeignKey(f'{Product.__tablename__}.id'))
    quantity = Column(Integer)


class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    cartId = Column(Integer, ForeignKey(f'{Cart.__tablename__}.id'))
    created = Column(DateTime, default=datetime.now)
    phone = Column(String(70))
    city = Column(String(50))
    street = Column(String(70))
    house = Column(Integer)
    apartment = Column(Integer)

