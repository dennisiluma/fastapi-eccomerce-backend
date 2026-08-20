from datetime import datetime

from pydantic import Field

from app.schemas.schema_base import SchemaBaseModel


class ReviewCreate(SchemaBaseModel):
    order_id: int
    product_id: int
    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5")
    comment: str


class ReviewResponse(SchemaBaseModel):

    id: int
    rating: int
    comment: str
    username: str
    created_at: datetime
    product_id: int
    user_id: int
