from typing import List

from fastapi import APIRouter, HTTPException
# from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from sqlalchemy import or_
# from sqlalchemy import func

# # from security import hash_password, encode_jwt, decode_jwt, check_password
from db import depends_db, Product, Brand, ProductCardOut, Category, CategoriesProductCardsOut, FullProductOut
# # from helpers import get_user_by_token


products_router = APIRouter(
    prefix='/products',
    tags=['Products']
)
# # oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/categories/add')


@products_router.get("/item/{product_id}", response_model=FullProductOut | None)
def get_prouct(product_id: int, session = Depends(depends_db)):
    
    product = session.query(
        Product.id,
        Product.name,
        Product.imageUrl,
        Product.price,
        Product.description,
        Brand.name.label('brand')
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
        Brand.name.label('brand')
    ).filter(
        Product.categoryId == category_id
    ).join(
        Brand, Product.brandId == Brand.id
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
        Brand.name.label('brand')
    ).filter(
        or_(
            Product.name.like(f'%{pattern}%'),
            Brand.name.like(f'%{pattern}%')
        )
    ).join(
        Brand, Product.brandId == Brand.id
    ).all()
    
    return products
