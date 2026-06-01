from fastapi import APIRouter,Depends
import httpx
from app.core.config import get_settings
from app.core.deps import get_current_user

router=APIRouter(prefix="/api/ai",tags=["AI"])
settings=get_settings()
def _ok():return settings.AI_API_KEY and settings.AI_API_KEY!="sk-your-api-key-here"

@router.post("/recommend")
async def recommend(user=Depends(get_current_user)):
    if not _ok():return {"recommendations":"AI not configured"}
    async with httpx.AsyncClient() as c:
        r=await c.post(f"{settings.AI_BASE_URL}/chat/completions",headers={"Authorization":f"Bearer {settings.AI_API_KEY}"},json={"model":settings.AI_MODEL,"messages":[{"role":"system","content":"Shopping recommendation AI"},{"role":"user","content":"Recommend products"}],"temperature":0.7},timeout=30)
        return {"recommendations":r.json()["choices"][0]["message"]["content"]}

@router.post("/sentiment")
async def sentiment(text:str):
    if not _ok():return {"sentiment":"neutral"}
    async with httpx.AsyncClient() as c:
        r=await c.post(f"{settings.AI_BASE_URL}/chat/completions",headers={"Authorization":f"Bearer {settings.AI_API_KEY}"},json={"model":settings.AI_MODEL,"messages":[{"role":"system","content":"Analyze sentiment"},{"role":"user","content":text}],"temperature":0.3},timeout=30)
        return {"result":r.json()["choices"][0]["message"]["content"]}
