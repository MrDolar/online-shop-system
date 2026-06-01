from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.deps import get_admin_user
from app.models.product import Product,Category

router=APIRouter(prefix="/api/products",tags=["Products"])

class ProductCreate(BaseModel):
    name:str;price:float;description:str="";category_id:Optional[int]=None;stock:int=0;image_url:str=""

@router.get("")
async def list_products(page:int=1,size:int=10,category_id:Optional[int]=None,keyword:Optional[str]=None,db:Session=Depends(get_db)):
    q=db.query(Product)
    if category_id:q=q.filter(Product.category_id==category_id)
    if keyword:q=q.filter(Product.name.contains(keyword))
    return {"total":q.count(),"items":[{"id":p.id,"name":p.name,"price":p.price,"stock":p.stock} for p in q.offset((page-1)*size).limit(size).all()]}

@router.post("")
async def create_product(req:ProductCreate,db:Session=Depends(get_db),admin=Depends(get_admin_user)):
    p=Product(**req.dict());db.add(p);db.commit();db.refresh(p);return {"id":p.id,"name":p.name}

@router.get("/{pid}")
async def get_product(pid:int,db:Session=Depends(get_db)):
    p=db.query(Product).filter(Product.id==pid).first()
    if not p:raise HTTPException(404,"Not found")
    return {"id":p.id,"name":p.name,"price":p.price,"description":p.description,"stock":p.stock}
