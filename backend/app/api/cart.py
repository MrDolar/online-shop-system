from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.cart import CartItem
from app.api.schemas import CartItemCreate, CartItemUpdate, CartItemResponse, CartResponse

router = APIRouter(prefix="/api/cart", tags=["购物车"])


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取购物车"""
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()

    items = []
    total_amount = 0.0
    total_items = 0

    for ci in cart_items:
        product = ci.product
        subtotal = product.price * ci.quantity
        items.append(CartItemResponse(
            id=ci.id,
            product_id=ci.product_id,
            product_name=product.name,
            product_price=product.price,
            product_image=product.image_url,
            quantity=ci.quantity,
            subtotal=subtotal
        ))
        total_amount += subtotal
        total_items += ci.quantity

    return CartResponse(
        items=items,
        total_amount=round(total_amount, 2),
        total_items=total_items
    )


@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    item_data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加商品到购物车"""
    # Check product exists
    product = db.query(Product).filter(Product.id == item_data.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if not product.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product is not available")
    if product.stock < item_data.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

    # Check if already in cart
    existing = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item_data.product_id
    ).first()

    if existing:
        existing.quantity += item_data.quantity
        if existing.quantity > product.stock:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
        db.commit()
        db.refresh(existing)
        return CartItemResponse(
            id=existing.id,
            product_id=existing.product_id,
            product_name=product.name,
            product_price=product.price,
            product_image=product.image_url,
            quantity=existing.quantity,
            subtotal=product.price * existing.quantity
        )

    cart_item = CartItem(
        user_id=current_user.id,
        product_id=item_data.product_id,
        quantity=item_data.quantity
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        product_name=product.name,
        product_price=product.price,
        product_image=product.image_url,
        quantity=cart_item.quantity,
        subtotal=product.price * cart_item.quantity
    )


@router.put("/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新购物车商品数量"""
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()

    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    product = cart_item.product
    if item_data.quantity > product.stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

    if item_data.quantity <= 0:
        db.delete(cart_item)
        db.commit()
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    cart_item.quantity = item_data.quantity
    db.commit()
    db.refresh(cart_item)

    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        product_name=product.name,
        product_price=product.price,
        product_image=product.image_url,
        quantity=cart_item.quantity,
        subtotal=product.price * cart_item.quantity
    )


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从购物车删除商品"""
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()

    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    db.delete(cart_item)
    db.commit()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空购物车"""
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
