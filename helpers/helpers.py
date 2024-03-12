from fastapi import HTTPException
from sqlalchemy.orm.session import Session
from sqlalchemy import func

# from db import User // need to create
from db import User, Cart, ProductOfCart
from security import decode_jwt


def get_user_by_token(token: str, session: Session) -> User:
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Для выполнения этого запроса вам нужно авторизоваться")
    user_id = payload['id']
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Для выполнения этого запроса вам нужно авторизоваться")
    return user


def getAmountOfCartItem(user: User, session: Session) -> int:
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