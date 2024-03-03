from typing import List
import os
import math
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, String
from sqlalchemy.orm import aliased, Session
from pydantic import BaseModel
import requests
import xlsxwriter

from db import depends_db, Cart, Order, ProductOfCart, Product, User
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
    
    
@orders_router.get('/xlsx_report')
def get_report(session: Session = Depends(depends_db)):
    
    query = session.query(
        Order.id,
        User.id.label('user_id'),
        User.username.label('user_username'),
        func.cast(Order.created, String),
        (func.concat('г. ', Order.city, ', ул. ', Order.street, ', д. ', func.cast(Order.house, String), ', кв. ', func.cast(Order.apartment, String))).label('address'),
        func.string_agg(Product.name + ' (x' + func.cast(ProductOfCart.quantity, String) + ')', ', ').label('products'),
        func.sum(Product.price * ProductOfCart.quantity).label('total_price')) \
    .join(Cart, Order.cartId == Cart.id) \
    .join(User, Cart.userId == User.id) \
    .join(ProductOfCart, ProductOfCart.cartId == Cart.id) \
    .join(Product, ProductOfCart.productId == Product.id) \
    .group_by(Order.id, User.id) \
    .order_by(Order.created)

    orders = query.all()
    
    workbook = xlsxwriter.Workbook('report.xlsx')
    worksheet = workbook.add_worksheet()
    
    headers = ['order_id', 'user_id', 'user_username', 'order_created', 'address', 'products', 'total_price']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
        
    for row, row_data in enumerate(orders, start=1):
        for col, cell_data in enumerate(row_data):
            worksheet.write(row, col, cell_data)
    
    worksheet.autofit()
    
    workbook.close()
    
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d-%m-%Y")
    
    return FileResponse('report.xlsx', filename=f"report_{formatted_date}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    


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
    
    # telegram notification
    products_of_order = session.query(
        Product.name,
        ProductOfCart.quantity
    ).select_from(
        ProductOfCart
    ).join(
        Product,
        ProductOfCart.productId == Product.id
    ).filter(
        ProductOfCart.cartId == order.cartId
    ).all()
    
    total_price = session.query(
        func.sum(ProductOfCart.quantity * Product.price)
    ).select_from(
        ProductOfCart
    ).join(
        Product,
        ProductOfCart.productId == Product.id
    ).filter(
        ProductOfCart.cartId == order.cartId
    ).scalar()
    
    if total_price >= 100:
        total_price = math.floor(total_price - (total_price * 0.1))
    
    procusts_string = '\n'.join([
        f'<i>{i+1}</i>. {name} <code>x{quantity}</code>' for i, (name, quantity) in enumerate(products_of_order)
    ])
    
    notification_text = f'<b>Новый заказ №<code>{order.id}</code></b>\n\n<i>Телефон заказчика</i>: <code>{order.phone}</code>\nАдрес доставки: <code>г. {order.city}. ул. {order.street}, д.{order.house}, кв.{order.apartment}</code>\n\n<i>Содержимое заказа</i>:\n{procusts_string}\n\nИтого: <code>{total_price}</code> BYN'
    
    r = requests.get(
        f'https://api.telegram.org/bot{os.getenv("TELEGRAM_BOT_TOKEN")}/sendMessage',
        params = {
            'chat_id': os.getenv("MANAGER_TELEGRAM_ID"),
            'text': notification_text,
            'parse_mode' : 'HTML'
        }
    )
    
    return {
        'ok': True
    }
    
    
    
    
    
    
    
