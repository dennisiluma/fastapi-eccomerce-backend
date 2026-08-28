from decimal import Decimal
from typing import List

from app.schemas.schema_base import SchemaBaseModel


class CartItemRead(SchemaBaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: Decimal
    product_image: str | None = None
    quantity: int
    subtotal: Decimal


class CartRead(SchemaBaseModel):
    id: int
    user_id: int
    items: List[CartItemRead]
    total_quantity: int
    total_price: Decimal


class AddToCartRequest(SchemaBaseModel):

    product_id: int
    quantity: int = 1
