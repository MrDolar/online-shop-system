from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.product import Product, Review
from app.api.schemas import (
    RecommendRequest, SentimentRequest, SentimentResponse,
    ChatRequest, ChatResponse, ProductResponse
)
from openai import AsyncOpenAI
import json

router = APIRouter(prefix="/api/ai", tags=["AI功能"])

# Conversation history storage (in production, use Redis or database)
conversations = {}


def get_ai_client():
    """Get OpenAI compatible client."""
    if not settings.AI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Set AI_API_KEY environment variable."
        )
    return AsyncOpenAI(
        api_key=settings.AI_API_KEY,
        base_url=settings.AI_BASE_URL
    )


@router.post("/recommend", response_model=List[dict])
async def recommend_products(
    request: RecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """智能商品推荐"""
    # Get user's order history for context
    from app.models.order import Order, OrderItem
    user_orders = db.query(Order).filter(
        Order.user_id == current_user.id,
        Order.status.in_(["paid", "delivered"])
    ).all()

    purchased_product_ids = set()
    for order in user_orders:
        for item in order.items:
            purchased_product_ids.add(item.product_id)

    # Get available products
    products = db.query(Product).filter(Product.is_active == True).all()

    if not products:
        return []

    # Build product list for AI
    product_list = []
    for p in products:
        product_list.append({
            "id": p.id,
            "name": p.name,
            "description": p.description or "",
            "price": p.price,
            "category_id": p.category_id,
            "rating": p.rating,
            "sales_count": p.sales_count
        })

    try:
        client = get_ai_client()

        # Get purchased product details for context
        purchased_names = []
        for pid in purchased_product_ids:
            p = db.query(Product).filter(Product.id == pid).first()
            if p:
                purchased_names.append(p.name)

        prompt = f"""你是一个商品推荐系统。根据用户的购买历史和可用商品列表，推荐最合适的商品。

用户购买过的商品: {', '.join(purchased_names) if purchased_names else '新用户，无购买记录'}

可用商品列表:
{json.dumps(product_list, ensure_ascii=False, indent=2)}

请推荐 {request.limit} 个商品，返回JSON格式数组，每个元素包含:
- id: 商品ID
- reason: 推荐理由（简短）

只返回JSON数组，不要其他文字。"""

        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()
        # Try to parse JSON from response
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        recommendations = json.loads(result_text)
        return recommendations

    except Exception as e:
        # Fallback: return top-selling products
        top_products = sorted(products, key=lambda p: p.sales_count, reverse=True)[:request.limit]
        return [{"id": p.id, "reason": "热门商品推荐"} for p in top_products]


@router.post("/analyze-sentiment", response_model=SentimentResponse)
async def analyze_sentiment(
    request: SentimentRequest,
    current_user: User = Depends(get_current_user)
):
    """商品评论情感分析"""
    try:
        client = get_ai_client()

        prompt = f"""分析以下商品评论的情感倾向。返回JSON格式:
{{
    "sentiment": "positive/negative/neutral",
    "score": 0.0到1.0之间的分数（1表示最正面），
    "analysis": "简短分析说明"
}}

评论内容: {request.text}

只返回JSON，不要其他文字。"""

        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )

        result_text = response.choices[0].message.content.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        result = json.loads(result_text)
        return SentimentResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """智能客服对话"""
    conversation_id = request.conversation_id or f"conv-{current_user.id}-{hash(request.message) % 10000}"

    # Get or create conversation history
    if conversation_id not in conversations:
        conversations[conversation_id] = [
            {
                "role": "system",
                "content": """你是一个专业的在线商城智能客服。你的职责是:
1. 帮助用户解答关于商品、订单、支付的问题
2. 提供购物建议和商品信息
3. 处理退换货咨询
4. 回答配送和物流问题

回复要友好、专业、简洁。如果问题超出能力范围，建议用户联系人工客服。"""
            }
        ]

    # Add user message
    conversations[conversation_id].append({
        "role": "user",
        "content": request.message
    })

    try:
        client = get_ai_client()

        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=conversations[conversation_id],
            temperature=0.7,
            max_tokens=1000
        )

        reply = response.choices[0].message.content

        # Add assistant response to history
        conversations[conversation_id].append({
            "role": "assistant",
            "content": reply
        })

        # Keep conversation history manageable (last 20 messages)
        if len(conversations[conversation_id]) > 21:
            conversations[conversation_id] = conversations[conversation_id][:1] + conversations[conversation_id][-20:]

        return ChatResponse(reply=reply, conversation_id=conversation_id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI chat failed: {str(e)}"
        )
