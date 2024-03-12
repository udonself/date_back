import os
from typing import List

from fastapi import APIRouter, HTTPException
# from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy import func

# # from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, Product, Brand, ProductCardOut, Category, CategoriesProductCardsOut, FullProductOut
from helpers import get_user_by_token


products_router = APIRouter(
    prefix='/products',
    tags=['Products']
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/orders/create')



class ShortProductInfo(BaseModel):
    id: int
    name: str


@products_router.get("/all", response_model=List[ShortProductInfo])
def get_short_products(session = Depends(depends_db)):
    
    products = session.query(
        Product.id,
        Product.name
    ).all()
    
    return products


class ProductToAddStock(BaseModel):
    product_id: int
    amount_to_add: int


@products_router.post("/add_stock")
def add_product_stock(data: ProductToAddStock, token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    if str(user.id) not in os.getenv('ADMIN_ID_LIST').split(","):
        raise HTTPException(status_code=403, detail="Access denied")
    
    product = session.query(
        Product
    ).filter(
        Product.id == data.product_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товара с таким id нет!")

    product.inStock += data.amount_to_add
    
    session.commit()
    
    return {
        "detail": f"Новое количество товара: {product.inStock}"
    }


@products_router.get("/item/{product_id}", response_model=FullProductOut | None)
def get_prouct(product_id: int, session = Depends(depends_db)):
    
    product = session.query(
        Product.id,
        Product.name,
        Product.imageUrl,
        Product.price,
        Product.description,
        Brand.name.label('brand'),
        Product.inStock
    ).filter(
        Product.id == product_id
    ).join(
        Brand, Product.brandId == Brand.id
    ).first()
    
    return product


@products_router.get("/{category_id}", response_model=CategoriesProductCardsOut)
def get_products(category_id: int, session = Depends(depends_db)):
    
    category_name = session.query(
        Category.name
    ).filter(
        Category.id == category_id
    ).first()[0]
    
    products = session.query(
        Product.id,
        Product.name,
        Product.imageUrl,
        Product.price,
        Brand.name.label('brand'),
        Product.inStock
    ).filter(
        Product.categoryId == category_id
    ).join(
        Brand, Product.brandId == Brand.id
    ).order_by(
        Product.inStock
    ).all()
    
    return {
        'category': category_name,
        'products': products
    }



@products_router.get("/search/{pattern}", response_model=List[ProductCardOut])
def get_products(pattern: str, session = Depends(depends_db)):

    products = session.query(
        Product.id,
        Product.name,
        Product.imageUrl,
        Product.price,
        Brand.name.label('brand'),
        Product.inStock
    ).filter(
        or_(
            Product.name.like(f'%{pattern}%'),
            Brand.name.like(f'%{pattern}%')
        )
    ).join(
        Brand, Product.brandId == Brand.id
    ).all()
    
    return products
