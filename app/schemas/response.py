from typing import Generic, TypeVar

from app.schemas.schema_base import SchemaBaseModel

T = TypeVar("T")


class ApiResponse(SchemaBaseModel, Generic[T]):

    status: int
    message: str
    data: T | None = None
