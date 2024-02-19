from typing import List

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func
from sqlalchemy.orm import aliased, Session
from pydantic import BaseModel

from db import depends_db, Cart, Order, ProductOfCart, Product
from helpers import get_user_by_token


orders_router = APIRouter(
    prefix='/orders',
    tags=['Orders']
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/orders/create')


class OrderOut(BaseModel):
    id: int
    amountOfProducts: int
    date: str
    totalPrice: float


@orders_router.get('/get', response_model=List[OrderOut])
def get_orders(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    orders = session.query(
        Order.id,
        func.sum(ProductOfCart.quantity).label('amountOfProducts'),
        Order.created.label('date'),
        func.sum(Product.price * ProductOfCart.quantity).label('totalPrice')
    ).select_from(
        Order
    ).join(
        Cart,
        Cart.id == Order.cartId
    ).filter(
        Cart.userId == user.id
    ).join(
        ProductOfCart,
        ProductOfCart.cartId == Cart.id
    ).join(
        Product,
        Product.id == ProductOfCart.productId
    ).group_by(
        Order.id
    ).all()
    
    return [
        OrderOut(id=id, amountOfProducts=amountOfProducts, date=date.strftime('%d-%m-%Y'), totalPrice=totalPrice) for (id, amountOfProducts, date, totalPrice) in orders
    ]
    
# export interface IOrder {
# id: number,
# amountOfProducts: number,
# date: string,
# totalPrice: number


class OrderData(BaseModel):
    phone: str
    city: str
    street: str
    house: int
    apartment: int


@orders_router.post("/create")
def add_to_cart(order_data: OrderData, token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    cart = session.query(
        Cart
    ).filter(
        Cart.userId == user.id,
        Cart.active == True
    ).first()
    
    order = Order(
        cartId = cart.id,
        phone = order_data.phone,
        city = order_data.city,
        street = order_data.street,
        house = order_data.house,
        apartment = order_data.apartment
    )
    
    session.add(order)
    cart.active = False
    session.commit()
    
    return {
        'ok': True
    }
    
    
    
    
    
    
    
