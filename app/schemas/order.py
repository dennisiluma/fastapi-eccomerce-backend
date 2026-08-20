from datetime import datetime
from decimal import Decimal
from typing import List
from pydantic import AliasPath, Field, computed_field, model_validator
from app.models.order import OrderStatus
from app.models.order import OrderStatus
from app.schemas.schema_base import SchemaBaseModel


class CheckoutRequest(SchemaBaseModel):
    shipping_address: str


class OrderStatusUpdate(SchemaBaseModel):
    status: OrderStatus


class OrderItemRead(SchemaBaseModel):
    id: int
    product_id: int
    
    product_name: str = Field(
        default="Unknown",
        validation_alias=AliasPath("product", "name"),
    )
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    is_reviewed: bool

    @computed_field
    def subtotal(self) -> Decimal:
        return Decimal(self.quantity) * self.unit_price



class OrderRead(SchemaBaseModel):
    id: int
    user_id: int
    total_price: Decimal
    status: OrderStatus
    shipping_address: str
    created_at: datetime
    items: List[OrderItemRead] = []