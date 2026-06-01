from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class RegisterReq(BaseModel):
    username: str
    email: str
    password: str

class LoginReq(BaseModel):
    username: str
    password: str

@router.post("/register")
async def register(req: RegisterReq, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(409, "Username exists")
    user = User(username=req.username, email=req.email, password_hash=get_password_hash(req.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "username": user.username}

@router.post("/login")
async def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_access_token({"sub": user.id}), "token_type": "bearer"}

@router.get("/me")
async def me(user = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
