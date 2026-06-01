from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.api.schemas import OverviewStats, SalesStats, ProductStats, UserStats

router = APIRouter(prefix="/api/statistics", tags=["数据统计"])


@router.get("/overview", response_model=OverviewStats)
async def get_statistics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据统计概览（需要管理员权限）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Sales statistics
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_(["paid", "shipped", "delivered"])
    ).scalar() or 0.0

    today_orders = db.query(func.count(Order.id)).filter(
        Order.created_at >= today
    ).scalar() or 0

    today_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= today,
        Order.status.in_(["paid", "shipped", "delivered"])
    ).scalar() or 0.0

    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0.0

    sales_stats = SalesStats(
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        today_orders=today_orders,
        today_revenue=round(today_revenue, 2),
        average_order_value=round(avg_order_value, 2)
    )

    # Product statistics
    total_products = db.query(func.count(Product.id)).scalar() or 0
    active_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
    low_stock_products = db.query(func.count(Product.id)).filter(
        Product.is_active == True,
        Product.stock < 10
    ).scalar() or 0

    top_selling_query = db.query(Product).filter(
        Product.is_active == True
    ).order_by(Product.sales_count.desc()).limit(10).all()

    top_selling = [
        {
            "id": p.id,
            "name": p.name,
            "sales_count": p.sales_count,
            "revenue": round(p.price * p.sales_count, 2)
        }
        for p in top_selling_query
    ]

    product_stats = ProductStats(
        total_products=total_products,
        active_products=active_products,
        low_stock_products=low_stock_products,
        top_selling=top_selling
    )

    # User statistics
    total_users = db.query(func.count(User.id)).scalar() or 0
    new_users_today = db.query(func.count(User.id)).filter(
        User.created_at >= today
    ).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0

    user_stats = UserStats(
        total_users=total_users,
        new_users_today=new_users_today,
        active_users=active_users
    )

    return OverviewStats(
        sales=sales_stats,
        products=product_stats,
        users=user_stats
    )


@router.get("/sales-trend")
async def get_sales_trend(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取销售趋势数据（需要管理员权限）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    start_date = datetime.utcnow() - timedelta(days=days)

    orders = db.query(
        func.date(Order.created_at).label("date"),
        func.count(Order.id).label("count"),
        func.sum(Order.total_amount).label("revenue")
    ).filter(
        Order.created_at >= start_date,
        Order.status.in_(["paid", "shipped", "delivered"])
    ).group_by(func.date(Order.created_at)).all()

    trend = [
        {
            "date": str(o.date),
            "orders": o.count,
            "revenue": round(float(o.revenue or 0), 2)
        }
        for o in orders
    ]

    return {"days": days, "trend": trend}


@router.get("/category-stats")
async def get_category_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取分类销售统计（需要管理员权限）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    from app.models.product import Category

    categories = db.query(Category).all()
    stats = []

    for cat in categories:
        product_count = db.query(func.count(Product.id)).filter(
            Product.category_id == cat.id
        ).scalar() or 0

        total_sales = db.query(func.sum(Product.sales_count)).filter(
            Product.category_id == cat.id
        ).scalar() or 0

        stats.append({
            "category_id": cat.id,
            "category_name": cat.name,
            "product_count": product_count,
            "total_sales": total_sales
        })

    return {"categories": stats}
