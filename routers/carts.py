from typing import List

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func
from sqlalchemy.orm import aliased, Session
from pydantic import BaseModel

from db import depends_db, User, Product, Cart, ProductOfCart, CartProductOut, Category, Brand
from helpers import get_user_by_token, getAmountOfCartItem


carts_router = APIRouter(
    prefix='/carts',
    tags=['Carts']
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/carts/add')


# @carts_router.get("/pis")
# def test(session: Session = Depends(depends_db)):
#     categories = session.query(
#         Category
#     ).all()
#     for c in categories:
#         print(f"""INSERT INTO categories (id, name, "imageUrl") VALUES ({c.id}, '{c.name}', '{c.imageUrl}');""")
    
#     brands = session.query(
#         Brand
#     ).all()
#     for b in brands:
#         print(f"INSERT INTO brands (id, name) VALUES ({b.id}, '{b.name}');")
    
#     products = session.query(
#         Product
#     ).all()
#     for p in products:
#         print(f"""INSERT INTO products (id, name, "imageUrl", price, description, "categoryId", "brandId", "inStock") VALUES ({p.id}, '{p.name}', '{p.imageUrl}', {p.price}, '{p.description}', {p.categoryId}, {p.brandId}, {p.inStock});""")


@carts_router.get("/amountOfItems")
def get_amount_if_cart_items(token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)

    return getAmountOfCartItem(user, session)


@carts_router.get("/cartAmount/{product_id}")
def get_amount_if_product_in_cart(product_id: int, token: str = Depends(oauth2_scheme), session: Session = Depends(depends_db)):
    
    user = get_user_by_token(token, session)
    
    cart_subquery = session.query(
        Cart.id.label('cart_id')
    ).filter(
        Cart.active == True,
        Cart.userId == user.id
    ).subquery()
    
    amount = session.query(
        ProductOfCart.quantity
    ).filter(
        ProductOfCart.productId == product_id,
        ProductOfCart.cartId == cart_subquery.c.cart_id
    ).scalar()
    
    if not amount:
        amount = 0
    
    return {
        'amount': amount
    }

    

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
        if product.inStock == 0:
        #     session.delete(product_of_cart)
        #     session.commit()
            raise HTTPException(status_code=404, detail={'message': 'В наличии нет столько товара!', 'new_quantity': 0})
        if product_to_add.quantity > 0:
            # if product_to_add.quantity > product.inStock:
            #     raise HTTPException(status_code=404, detail="В наличии нет столько товара!")
            product_of_cart = ProductOfCart(
                cartId = cart.id,
                productId = product.id,
                quantity = product_to_add.quantity
            )
            session.add(product_of_cart)
            session.commit()
            cart_items_amount = getAmountOfCartItem(user, session)
            return {'new_quantity': product_to_add.quantity, 'total_items': cart_items_amount}
        else:
            cart_items_amount = getAmountOfCartItem(user, session)
            return {'new_quantity': 0, 'total_items': cart_items_amount}
    
    else: # если товар уже есть в корзине
        if (product_of_cart.quantity + product_to_add.quantity) > 0:
            if (product_of_cart.quantity + product_to_add.quantity) > product.inStock:
                if product.inStock == 0:
                    session.delete(product_of_cart)
                    session.commit()
                elif product_of_cart.quantity >= product.inStock:
                    product_of_cart.quantity = product.inStock
                    session.commit()
                raise HTTPException(status_code=404, detail={'message': 'В наличии нет столько товара!', 'new_quantity': product_of_cart.quantity})
            product_of_cart.quantity += product_to_add.quantity
            session.commit()
            cart_items_amount = getAmountOfCartItem(user, session)
            return {'new_quantity': product_of_cart.quantity, 'total_items': cart_items_amount}
        else:
            session.delete(product_of_cart)
            session.commit()
    
    cart_items_amount = getAmountOfCartItem(user, session)
    return {'new_quantity': 0, 'total_items': cart_items_amount}
    
    
    
    
    
