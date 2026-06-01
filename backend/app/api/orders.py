from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.cart import CartItem
from app.models.order import Order, OrderItem, Payment
from app.api.schemas import OrderCreate, OrderResponse, PaymentCreate, PaymentResponse

router = APIRouter(prefix="/api", tags=["订单"])


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从购物车创建订单"""
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    # Validate stock
    order_items_data = []
    total_amount = 0.0

    for ci in cart_items:
        product = ci.product
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is no longer available"
            )
        if product.stock < ci.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'"
            )
        subtotal = product.price * ci.quantity
        order_items_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "product_price": product.price,
            "quantity": ci.quantity,
            "subtotal": subtotal
        })
        total_amount += subtotal

    # Create order
    order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    order = Order(
        order_number=order_number,
        user_id=current_user.id,
        total_amount=round(total_amount, 2),
        shipping_address=order_data.shipping_address,
        phone=order_data.phone,
        remark=order_data.remark
    )
    db.add(order)
    db.flush()

    # Create order items and update stock
    for item_data in order_items_data:
        order_item = OrderItem(order_id=order.id, **item_data)
        db.add(order_item)

        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock -= item_data["quantity"]
        product.sales_count += item_data["quantity"]

    # Clear cart
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()

    db.commit()
    db.refresh(order)
    return order


@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的订单列表"""
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).all()
    return orders


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取订单详情"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.put("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消订单"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status not in ["pending"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order cannot be cancelled")

    # Restore stock
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
            product.sales_count -= item.quantity

    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order


# ==================== Payment Endpoints ====================

@router.post("/payments/{order_id}", response_model=PaymentResponse)
async def create_payment(
    order_id: int,
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发起支付（模拟）"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is not pending payment")

    # Check if payment already exists
    existing_payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if existing_payment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already exists")

    # Simulate payment (always success in demo)
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    payment = Payment(
        order_id=order_id,
        amount=order.total_amount,
        method=payment_data.method,
        status="success",
        transaction_id=transaction_id,
        paid_at=datetime.utcnow()
    )
    db.add(payment)

    # Update order status
    order.status = "paid"
    order.paid_at = datetime.utcnow()

    db.commit()
    db.refresh(payment)
    return payment


@router.get("/payments/{order_id}", response_model=PaymentResponse)
async def get_payment(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取支付信息"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment
