from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import categories_router, products_router, users_router, carts_router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


for router in (categories_router, products_router, users_router, carts_router):
    app.include_router(router)