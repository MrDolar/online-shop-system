from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.product import Order,OrderItem,CartItem,Product

router=APIRouter(prefix="/api/orders",tags=["Orders"])

@router.post("")
async def create_order(user=Depends(get_current_user),db:Session=Depends(get_db)):
    cart_items=db.query(CartItem).filter(CartItem.user_id==user.id).all()
    if not cart_items:raise HTTPException(400,"Cart is empty")
    order=Order(user_id=user.id,total=0,status="pending",created_at=datetime.utcnow())
    db.add(order);db.flush()
    total=0
    for ci in cart_items:
        p=db.query(Product).filter(Product.id==ci.product_id).first()
        if p and p.stock>=ci.quantity:
            p.stock-=ci.quantity;total+=p.price*ci.quantity
            db.add(OrderItem(order_id=order.id,product_id=p.id,quantity=ci.quantity,price=p.price))
        else:raise HTTPException(400,"Insufficient stock")
    order.total=total
    db.query(CartItem).filter(CartItem.user_id==user.id).delete()
    db.commit();return {"order_id":order.id,"total":total}

@router.get("")
async def list_orders(user=Depends(get_current_user),db:Session=Depends(get_db)):
    orders=db.query(Order).filter(Order.user_id==user.id).order_by(Order.created_at.desc()).all()
    return {"items":[{"id":o.id,"total":o.total,"status":o.status} for o in orders]}

@router.put("/{oid}/pay")
async def pay_order(oid:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    o=db.query(Order).filter(Order.id==oid,Order.user_id==user.id).first()
    if not o:raise HTTPException(404,"Not found")
    o.status="paid";db.commit();return {"message":"Paid"}
