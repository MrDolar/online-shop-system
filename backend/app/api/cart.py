from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.product import CartItem,Product

router=APIRouter(prefix="/api/cart",tags=["Cart"])

class CartAdd(BaseModel):
    product_id:int;quantity:int=1

@router.get("")
async def get_cart(user=Depends(get_current_user),db:Session=Depends(get_db)):
    items=db.query(CartItem).filter(CartItem.user_id==user.id).all()
    result=[]
    for i in items:
        p=db.query(Product).filter(Product.id==i.product_id).first()
        result.append({"id":i.id,"product_id":i.product_id,"name":p.name if p else "","price":p.price if p else 0,"quantity":i.quantity})
    return {"items":result}

@router.post("")
async def add_to_cart(req:CartAdd,user=Depends(get_current_user),db:Session=Depends(get_db)):
    existing=db.query(CartItem).filter(CartItem.user_id==user.id,CartItem.product_id==req.product_id).first()
    if existing:existing.quantity+=req.quantity
    else:db.add(CartItem(user_id=user.id,product_id=req.product_id,quantity=req.quantity))
    db.commit();return {"message":"Added"}

@router.delete("/{item_id}")
async def remove_from_cart(item_id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    item=db.query(CartItem).filter(CartItem.id==item_id,CartItem.user_id==user.id).first()
    if not item:raise HTTPException(404,"Not found")
    db.delete(item);db.commit();return {"message":"Removed"}
