import secrets
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional
from db import Database
from models import User, Token, UserRole

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

db = Database()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole

class UserLogin(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    token: str

def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/register", response_model=TokenOut)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_create.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user_create.password)
    user = User(username=user_create.username, hashed_password=hashed_password, role=user_create.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    token_str = secrets.token_hex(32)
    token = Token(token=token_str, user_id=user.id)
    db.add(token)
    db.commit()
    return {"token": token_str}

@router.post("/login", response_model=TokenOut)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_login.username).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    # Generate new token
    token_str = secrets.token_hex(32)
    token = Token(token=token_str, user_id=user.id)
    db.add(token)
    db.commit()
    return {"token": token_str}

def get_current_user(token: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token header missing")
    db_token = db.query(Token).filter(Token.token == token).first()
    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return db_token.user

def require_role(required_roles):
    def role_checker(user: User = Depends(get_current_user)):
        if user.role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker
