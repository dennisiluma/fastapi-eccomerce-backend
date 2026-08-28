from fastapi import APIRouter
from .auth import router as auth_api
from .users import router as users_api
from .category import router as category_api
from .product import router as product_api
from .cart import router as cart_api
from .order import router as order_api
from .payment import router as payment_api
from .review import router as review_api
from .report import router as report_api

api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    return {"message": "APP Health Is Working Fine"}


api_router.include_router(auth_api)
api_router.include_router(users_api)
api_router.include_router(category_api)
api_router.include_router(product_api)
api_router.include_router(cart_api)
api_router.include_router(order_api)
api_router.include_router(payment_api)
api_router.include_router(review_api)
api_router.include_router(report_api)
