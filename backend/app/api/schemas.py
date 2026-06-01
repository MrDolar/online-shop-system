from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ==================== User Schemas ====================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ==================== Category Schemas ====================

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]

    class Config:
        from_attributes = True


# ==================== Product Schemas ====================

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    stock: int = 0
    category_id: Optional[int] = None
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    original_price: Optional[float]
    stock: int
    category_id: Optional[int]
    image_url: Optional[str]
    is_active: bool
    sales_count: int
    rating: float
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Cart Schemas ====================

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: float
    product_image: Optional[str]
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_amount: float
    total_items: int


# ==================== Order Schemas ====================

class OrderCreate(BaseModel):
    shipping_address: str
    phone: str
    remark: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: float
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    total_amount: float
    status: str
    shipping_address: str
    phone: str
    remark: Optional[str]
    items: List[OrderItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Payment Schemas ====================

class PaymentCreate(BaseModel):
    method: str  # alipay, wechat, credit_card


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    method: str
    status: str
    transaction_id: Optional[str]
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Review Schemas ====================

class ReviewCreate(BaseModel):
    product_id: int
    rating: int
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    rating: int
    comment: Optional[str]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== AI Schemas ====================

class RecommendRequest(BaseModel):
    user_id: Optional[int] = None
    product_id: Optional[int] = None
    limit: int = 5


class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    sentiment: str
    score: float
    analysis: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


# ==================== Statistics Schemas ====================

class SalesStats(BaseModel):
    total_orders: int
    total_revenue: float
    today_orders: int
    today_revenue: float
    average_order_value: float


class ProductStats(BaseModel):
    total_products: int
    active_products: int
    low_stock_products: int
    top_selling: List[dict]


class UserStats(BaseModel):
    total_users: int
    new_users_today: int
    active_users: int


class OverviewStats(BaseModel):
    sales: SalesStats
    products: ProductStats
    users: UserStats
