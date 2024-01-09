
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from db import depends_db, ReviewToCreate, Review
from helpers import get_user_by_token


reviews_router = APIRouter(tags=['Reviews'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/reviews/create')

    
@reviews_router.post("/reviews/create")
def create_review(review_data: ReviewToCreate, token: str = Depends(oauth2_scheme), session = Depends(depends_db)):
    user = get_user_by_token(token, session)
    new_review = Review(
        to_id = review_data.to_id,
        from_id = user.id,
        content = review_data.content,
        rating = review_data.rating
    )
    session.add(new_review)
    session.commit()
    return new_review