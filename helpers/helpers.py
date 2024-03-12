from fastapi import HTTPException
from sqlalchemy.orm.session import Session
from sqlalchemy import func
import xlsxwriter

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

def prepare_workbook(report_number: int, title: str, headers: list, data):
    workbook = xlsxwriter.Workbook('report.xlsx')
    worksheet = workbook.add_worksheet()
    
    wrap = workbook.add_format({'text_wrap': True})
    wrap.set_bold()
    wrap.set_align('center')
    worksheet.write(0, 0, f'Отчет №{report_number}\n{title}', wrap)
    
    value_wrap = workbook.add_format()
    value_wrap.set_align('left')
    value_wrap.set_border()
    
    title_wrap = workbook.add_format()
    title_wrap.set_bold()
    title_wrap.set_border()
    
    footer_wrap = workbook.add_format()
    footer_wrap.set_bold()
    footer_wrap.set_align('right')
    
    print_wrap = workbook.add_format()
    print_wrap.set_align('left')
    print_wrap.set_font_size(16)
    print_wrap.set_bottom()
    
    for col, header in enumerate(headers):
        worksheet.write(2, col, header, title_wrap)
        
    for row, row_data in enumerate(data, start=3):
        for col, cell_data in enumerate(row_data):
            worksheet.write(row, col, cell_data, value_wrap)
    
    footer_row_number = len(data)
    worksheet.write(footer_row_number+4, 0, 'ООО "Joma Shop"', footer_wrap)
    worksheet.write(footer_row_number+5, 0, 'М.П.', print_wrap)
    
    worksheet.autofit()
    
    return (workbook, worksheet)