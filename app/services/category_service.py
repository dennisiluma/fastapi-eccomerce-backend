from sqlalchemy import select
from fastapi import status
from app.core.exceptions import ApiException
from app.models.category import Category
from app.schemas.category import CategorySchema

from sqlalchemy.ext.asyncio import AsyncSession


async def create_category(db: AsyncSession, category_data: CategorySchema) -> Category:

    existing_category = await db.scalar(
        select(Category.id).where(Category.name == category_data.name)
    )
    if existing_category:
        raise ApiException("Category already exists", status.HTTP_400_BAD_REQUEST)

    db_category = Category(**category_data.model_dump())

    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


async def get_all_categories(db: AsyncSession) -> list[Category]:

    result = await db.scalars(select(Category))
    return list(result.all())


async def get_category_by_id(db: AsyncSession, category_id: int) -> Category:

    category = await db.get(Category, category_id)
    if not category:
        raise ApiException("Category not found", status.HTTP_404_NOT_FOUND)
    return category


async def update_category(db: AsyncSession, update_data: CategorySchema) -> Category:
    db_category = await get_category_by_id(db, update_data.id)

    data = update_data.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(db_category, key, value)

    await db.commit()
    await db.refresh(db_category)
    return db_category



async def delete_category(db: AsyncSession, category_id: int) -> bool:
    db_category = await get_category_by_id(db, category_id)

    await db.delete(db_category)
    await db.commit()
    return True