from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class CategoryOut(BaseModel):
    id: int
    name: str
    imageUrl: str


class ProductCardOut(BaseModel):
    id: int
    name: str
    imageUrl: str
    price: float
    brand: str


class CategoriesProductCardsOut(BaseModel):
    category: str
    products: List[ProductCardOut]


class FullProductOut(BaseModel):
    id: int
    name: str
    imageUrl: str
    price: float
    brand: str
    description: str


class CartProductOut(BaseModel):
    id: int
    name: str
    imageUrl: str
    price: float
    quantity: int
    totalPrice: float
    
    

    