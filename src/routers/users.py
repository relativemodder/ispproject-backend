from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from db import Database
from models import User, UserRole
from auth import require_role, get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

db = Database()

from typing import Optional

class InstallerInfo(BaseModel):
    id: int
    name: str
    contact_info: Optional[str] = None

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    id: int
    username: str
    role: UserRole
    installer: Optional[InstallerInfo] = None

    class Config:
        orm_mode = True

def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()

@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), user=Depends(require_role([UserRole.ADMINISTRATOR]))):
    users = db.query(User).all()
    return users

@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user
