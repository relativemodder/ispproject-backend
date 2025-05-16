from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
from db import Database
from models import Installer, UserRole
from auth import require_role
from routers.users import UserOut

router = APIRouter(
    prefix="/installers",
    tags=["Installers"]
)

db = Database()

class InstallerIn(BaseModel):
    name: str
    contact_info: Optional[str] = None
    user_id: Optional[int] = None

class InstallerOut(BaseModel):
    id: int
    name: str
    contact_info: Optional[str] = None
    user_id: Optional[int] = None
    user: Optional[UserOut] = None

    class Config:
        orm_mode = True

def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()

@router.get("/", response_model=List[InstallerOut])
def list_installers(db: Session = Depends(get_db), user=Depends(require_role([UserRole.ADMINISTRATOR, UserRole.DISPATCHER, UserRole.INSTALLER]))):
    installers = db.query(Installer).options(joinedload(Installer.user)).all()
    return installers

@router.post("/", response_model=InstallerOut, status_code=status.HTTP_201_CREATED)
def create_installer(installer_in: InstallerIn, db: Session = Depends(get_db), user=Depends(require_role([UserRole.ADMINISTRATOR]))):
    installer = Installer(name=installer_in.name, contact_info=installer_in.contact_info, user_id=installer_in.user_id)
    db.add(installer)
    db.commit()
    db.refresh(installer)
    return installer
