
from app.schemas.schema_base import SchemaBaseModel


class CategorySchema(SchemaBaseModel):
    id: int | None = None
    name: str
    description: str | None = None

