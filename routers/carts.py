from typing import List

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func
from sqlalchemy.orm import aliased, Session
from pydantic import BaseModel

from db import depends_db, User, Product, Cart, ProductOfCart, CartProductOut
from helpers import get_user_by_token


carts_router = APIRouter(
    prefix='/carts',
    tags=['Carts']
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/carts/add')


@carts_router.get("/amountOfItems")
def get_amount_of_cart_items(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    cart = session.query(
        Cart
    ).filter(
        Cart.userId == user.id,
        Cart.active == True
    ).first()
    
    if not cart:
        return 0
    
    amount = session.query(
        func.sum(ProductOfCart.quantity).label('total_items')
    ).select_from(
        ProductOfCart
    ).filter(
        ProductOfCart.cartId == cart.id
    ).scalar()
    
    return amount


@carts_router.get("/get", response_model=List[CartProductOut])
def get_cart(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    # получаем корзину
    cart = session.query(
        Cart
    ).filter(
        Cart.userId == user.id,
        Cart.active == True
    ).first()
    
    if not cart:
        return []
    
    products_in_cart = session.query(
        Product.id,
        Product.name,
        Product.imageUrl,
        Product.price,
        ProductOfCart.quantity,
        func.sum(Product.price * ProductOfCart.quantity).label('total_price')
    ).select_from(
        ProductOfCart
    ).filter(
        ProductOfCart.cartId == cart.id
    ).join(
        Product,
        Product.id == ProductOfCart.productId
    ).group_by(
        Product.id, ProductOfCart.id
    ).all()
    
    return [
        CartProductOut(id=id, name=name, imageUrl=image, price=price, quantity=quantity, totalPrice=totalPrice) for (id, name, image, price, quantity, totalPrice) in products_in_cart
    ]


class ProductToAdd(BaseModel):
    id: int
    quantity: int


@carts_router.post("/add")
def add_to_cart(product_to_add: ProductToAdd, token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    # получаем корзину
    cart = session.query(
        Cart
    ).filter(
        Cart.userId == user.id,
        Cart.active == True
    ).first()
    
    # создаем корзину если ее еще нет
    if not cart:
        cart = Cart(
            userId = user.id,
            active = True
        )
        session.add(cart)
        session.commit()
    
    # получение товара, который мы пытаемся добавить в корзину для последующей проверки
    product = session.query(
        Product
    ).filter(
        Product.id == product_to_add.id
    ).first()
    
    # проверка на существование такого товара
    if not product:
        raise HTTPException(status_code=404, detail="Такого товара нет")

    # получение содержимого корзины с выбранным товаром
    product_of_cart = session.query(
        ProductOfCart
    ).filter(
        ProductOfCart.cartId == cart.id,
        ProductOfCart.productId == product.id
    ).first()
    
    # если этот товар еще не в корзине, то создаем запись с его содержанием
    if not product_of_cart:
        if product_to_add.quantity > 0:
            product_of_cart = ProductOfCart(
                cartId = cart.id,
                productId = product.id,
                quantity = product_to_add.quantity
            )
            session.add(product_of_cart)
            session.commit()
            return {'new_quantity': product_to_add.quantity}
        else:
            return {'new_quantity': 0}
    
    else:
        if (product_of_cart.quantity + product_to_add.quantity) > 0:
            product_of_cart.quantity += product_to_add.quantity
            session.commit()
            return {'new_quantity': product_of_cart.quantity}
        else:
            session.delete(product_of_cart)
            session.commit()
    
    return {'new_quantity': 0}
    
    
    
    
    
