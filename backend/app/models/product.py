from datetime import datetime
from sqlalchemy import Column,Integer,String,Float,DateTime,ForeignKey,Text
from app.core.database import Base

class Category(Base):
    __tablename__="categories"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(50),unique=True,nullable=False)

class Product(Base):
    __tablename__="products"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(200),nullable=False,index=True)
    price=Column(Float,nullable=False)
    description=Column(Text,default="")
    category_id=Column(Integer,ForeignKey("categories.id"),nullable=True)
    stock=Column(Integer,default=0)
    image_url=Column(String(500),default="")
    created_at=Column(DateTime,default=datetime.utcnow)

class CartItem(Base):
    __tablename__="cart_items"
    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    product_id=Column(Integer,ForeignKey("products.id"),nullable=False)
    quantity=Column(Integer,default=1)

class Order(Base):
    __tablename__="orders"
    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    total=Column(Float,default=0)
    status=Column(String(20),default="pending")
    created_at=Column(DateTime,default=datetime.utcnow)

class OrderItem(Base):
    __tablename__="order_items"
    id=Column(Integer,primary_key=True,index=True)
    order_id=Column(Integer,ForeignKey("orders.id"),nullable=False)
    product_id=Column(Integer,ForeignKey("products.id"),nullable=False)
    quantity=Column(Integer,default=1)
    price=Column(Float,default=0)
