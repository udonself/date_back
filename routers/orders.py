from typing import List
import os
import math
from datetime import datetime
import random

from fastapi import APIRouter, HTTPException
from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, select, String
from sqlalchemy import update
from sqlalchemy.orm import aliased, Session
from pydantic import BaseModel
import requests
import xlsxwriter

from db import depends_db, Cart, Order, ProductOfCart, Product, User, Brand, StockReplenishment
from helpers import get_user_by_token, prepare_workbook


orders_router = APIRouter(
    prefix='/orders',
    tags=['Orders']
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/orders/create')


@orders_router.get('/xlsx/sales/{start_date}/{end_date}')
def get_sales(start_date: str, end_date: str, session: Session = Depends(depends_db)):

    sold_products_subquery = session.query(
        ProductOfCart.productId,
        ProductOfCart.quantity
    ).select_from(
        ProductOfCart
    ).join(
        Cart, ProductOfCart.cartId == Cart.id
    ).join(
        Order, Cart.id == Order.cartId
    ).filter(
        Order.created >= start_date, Order.created <= end_date
    ).subquery()
    
    products = session.query(
        # Product.id,
        Product.name,
        Product.inStock,
        func.coalesce(func.sum(sold_products_subquery.c.quantity), 0).label('TotalSold')
    ).select_from(
        Product
    ).join(
        sold_products_subquery,
        sold_products_subquery.c.productId == Product.id,
        isouter=True
    ).group_by(
        Product.id
    ).order_by(
        func.coalesce(func.sum(sold_products_subquery.c.quantity), 0).desc()
    ).all()

        
    workbook, worksheet = prepare_workbook(
        report_number=random.randint(10000, 99999),
        title=f'Количество продаж и остаток с {start_date} по {end_date}',
        headers=['Товар', 'В наличии', f'Продано'],
        data=products
    )
    workbook.close()
    
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d-%m-%Y")
    
    return FileResponse('report.xlsx', filename=f"report_{formatted_date}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    

@orders_router.get('/xlsx/orders/{start_date}/{end_date}')
def get_orders(start_date: str, end_date: str, session: Session = Depends(depends_db)):
    
    query = session.query(
        Order.id,
        # User.id.label('user_id'),
        # User.username.label('user_username'),
        func.cast(Order.created, String),
        (func.concat('г. ', Order.city, ', ул. ', Order.street, ', д. ', func.cast(Order.house, String), ', кв. ', func.cast(Order.apartment, String))).label('address'),
        func.string_agg(Product.name + ' (x' + func.cast(ProductOfCart.quantity, String) + ')', ', ').label('products'),
        func.sum(Product.price * ProductOfCart.quantity).label('total_price')) \
    .filter(Order.created >= start_date, Order.created <= end_date) \
    .join(Cart, Order.cartId == Cart.id) \
    .join(User, Cart.userId == User.id) \
    .join(ProductOfCart, ProductOfCart.cartId == Cart.id) \
    .join(Product, ProductOfCart.productId == Product.id) \
    .group_by(Order.id, User.id) \
    .order_by(Order.created)

    orders = query.all()
    
    workbook, worksheet = prepare_workbook(
        report_number=random.randint(10000, 99999),
        title=f'Детализация заказов с {start_date} по {end_date}',
        headers = ['Айди заказа', 'Дата', 'Адрес', 'Товары', 'Итоговая цена'],
        data=orders
    )
    workbook.close()
    
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d-%m-%Y")
    
    return FileResponse('report.xlsx', filename=f"report_{formatted_date}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@orders_router.get('/xlsx/repleishments/{start_date}/{end_date}')
def get_repleishments(start_date: str, end_date: str, session: Session = Depends(depends_db)):
    
    query = session.query(
        StockReplenishment.id,
        func.cast(StockReplenishment.created, String),
        Product.name,
        StockReplenishment.quantity
    ).select_from(
        StockReplenishment
    ).join(
        Product,
        Product.id == StockReplenishment.productId
    ).filter(
        StockReplenishment.created >= start_date, StockReplenishment.created <= end_date
    ).order_by(
        StockReplenishment.created.desc()
    )

    orders = query.all()
    
    workbook, worksheet = prepare_workbook(
        report_number=random.randint(10000, 99999),
        title=f'Пополнения наличия с {start_date} по {end_date}',
        headers = ['Айди пополнения', 'Дата', 'Товар', 'Количество'],
        data=orders
    )
    
    workbook.close()
    
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d-%m-%Y")
    
    return FileResponse('report.xlsx', filename=f"report_{formatted_date}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    

@orders_router.get('/xlsx/repleishments_sum/{start_date}/{end_date}')
def get_repleishments(start_date: str, end_date: str, session: Session = Depends(depends_db)):
    
    query = session.query(
        # StockReplenishment.id,
        # StockReplenishment.created,
        Product.name,
        func.sum(StockReplenishment.quantity).label('total_amount')
    ).select_from(
        StockReplenishment
    ).join(
        Product,
        Product.id == StockReplenishment.productId
    ).filter(
        StockReplenishment.created >= start_date, StockReplenishment.created <= end_date
    ).group_by(
        Product.id
    ).order_by(
        func.sum(StockReplenishment.quantity).desc()
    )

    orders = query.all()
    
    workbook, worksheet = prepare_workbook(
        report_number=random.randint(10000, 99999),
        title=f'Пополнения наличия с {start_date} по {end_date}',
        headers = ['Товар', 'Количество'],
        data=orders
    )
    
    workbook.close()
    
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d-%m-%Y")
    
    return FileResponse('report.xlsx', filename=f"report_{formatted_date}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    
    

class DataToChangeStatus(BaseModel):
    order_id: int
    status: str


@orders_router.post('/change_status')
def change_order_status(data: DataToChangeStatus, token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    if str(user.id) not in os.getenv('ADMIN_ID_LIST').split(","):
        raise HTTPException(status_code=403, detail="Access denied")
    
    order = session.query(
        Order
    ).filter(
        Order.id == data.order_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказа с таким id нет!")

    order.status = data.status
    
    session.commit()
    
    return {
        "detail":"Статус заказа был успешно изменен!"
    }
    

class OrderOut(BaseModel):
    id: int
    amountOfProducts: int
    date: str
    totalPrice: float
    status: str
    
    
@orders_router.get('/get', response_model=List[OrderOut])
def get_orders(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    orders = session.query(
        Order.id,
        func.sum(ProductOfCart.quantity).label('amountOfProducts'),
        Order.created.label('date'),
        func.sum(Product.price * ProductOfCart.quantity).label('totalPrice'),
        Order.status
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
    ).order_by(
        Order.created.desc()
    ).all()
    
    return [
        OrderOut(
            id=id,
            amountOfProducts=amountOfProducts,
            date=date.strftime('%d-%m-%Y'),
            totalPrice=totalPrice if totalPrice < 100 else math.floor(totalPrice - totalPrice * 0.1),
            status=status
        ) for (id, amountOfProducts, date, totalPrice, status) in orders
    ]


class OrderItem(BaseModel):
    name: str
    brand: str
    imageUrl: str
    quantity: int
    price: float


class FullOrderData(BaseModel):
    items: List[OrderItem]
    totalPrice: float


@orders_router.get('/s/{order_id}', response_model=FullOrderData)
def get_order(order_id: int, token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    subquery = session.query(
        Cart.id.label('cartId')
    ).select_from(
        Order
    ).join(
        Cart, Order.cartId == Cart.id
    ).filter(
        Order.id == order_id,
        Cart.userId == user.id
    ).subquery()
    
    order_products = session.query(
        Product.name,
        Product.imageUrl,
        Brand.name.label('brand'),
        ProductOfCart.quantity,
        func.sum(Product.price * ProductOfCart.quantity).label('price')
    ).select_from(
        ProductOfCart
    ).join(
        Product,
        Product.id == ProductOfCart.productId
    ).join(
        Brand,
        Brand.id == Product.brandId
    ).group_by(
        Product.name,
        Product.imageUrl,
        Brand.name,
        ProductOfCart.quantity
    ).filter(
        ProductOfCart.cartId == subquery.c.cartId
    ).all()
    
    products_out = [OrderItem(
        name=name, imageUrl=imageUrl, brand=brand, quantity=quantity, price=price
    ) for (name, imageUrl, brand, quantity, price) in order_products]
    
    total_price = sum(map(lambda item: item.price, products_out))
    if total_price >= 100:
        total_price = math.floor(total_price - total_price * 0.1)
    
    return FullOrderData(
        items=products_out,
        totalPrice=total_price
    )
    


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
    
    ###
    # удаляем наличие заказанного товара
    products_of_order_subquery = session.query(
        ProductOfCart.productId,
        func.sum(ProductOfCart.quantity).label('total_quantity')
    ).filter(
        ProductOfCart.cartId == order.cartId
    ).group_by(
        ProductOfCart.productId
    ).subquery()

    # Обновляем количество товаров в наличии для каждого продукта
    stmt = update(Product).\
        values(inStock=Product.inStock - products_of_order_subquery.c.total_quantity).\
        where(Product.id == products_of_order_subquery.c.productId)

    session.execute(stmt)
    session.commit()
    ###
        
    
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
    
    
    
    
    
    
    
