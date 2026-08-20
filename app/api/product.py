from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import db_session
from app.api.dependencies import get_current_admin
from app.schemas.product import ProductDetail, ProductRead, ProductUpdate
from app.schemas.response import ApiResponse
from app.services.product_service import (
    create_product,
    delete_product,
    get_all_products,
    get_product_by_id,
    update_product,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", status_code=status.HTTP_200_OK)
async def list_products(
    category_id: int | None = None, db: AsyncSession = Depends(db_session)
) -> ApiResponse[list[ProductRead]]:

    products = await get_all_products(db, category_id)

    return ApiResponse[list[ProductRead]](
        status=status.HTTP_200_OK,
        message="Products fetched successfully",
        data=products,
    )


@router.get("/{product_id}", status_code=status.HTTP_200_OK)
async def get_product(
    product_id: int, db: AsyncSession = Depends(db_session)
) -> ApiResponse[ProductDetail]:
    product = await get_product_by_id(db, product_id)

    return ApiResponse[ProductDetail](
        status=status.HTTP_200_OK, message="Product details", data=product
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock_quantity: int = Form(...),
    category_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(db_session),
    _=Depends(get_current_admin),
) -> ApiResponse[ProductRead]:

    product = await create_product(
        db=db,
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category_id=category_id,
        file=file,
    )

    return ApiResponse[ProductRead](
        status=status.HTTP_201_CREATED, message="Product created", data=product
    )




@router.put("/update", status_code=status.HTTP_200_OK)
async def edit_product(
    id: int = Form(...),
    name: str | None = Form(None),
    description: str | None = Form(None),
    price: float | None = Form(None),
    stock_quantity: int | None = Form(None),
    category_id: int | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(db_session),
    _=Depends(get_current_admin),
) -> ApiResponse[ProductRead]:
    update_data = ProductUpdate(
        id=id,
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category_id=category_id,
    )
    product = await update_product(db, update_data, file)

    return ApiResponse[ProductRead](
        status=status.HTTP_200_OK, message="Product updated", data=product
    )




@router.delete("/delete/{product_id}", status_code=status.HTTP_200_OK)
async def remove_product(
    product_id: int,
    db: AsyncSession = Depends(db_session),
    _=Depends(get_current_admin),
) -> ApiResponse[None]:

    await delete_product(db, product_id)

    return ApiResponse[None](status=status.HTTP_200_OK, message="Product deleted")
