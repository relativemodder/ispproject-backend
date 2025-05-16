from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from db import Database
from models import Order, Installer, Comment, OrderStatus
from auth import get_current_user, require_role
from models import UserRole

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

db = Database()

# Pydantic schemas

class OrderCreate(BaseModel):
    address: str
    account_number: str
    contact_details: str

class OrderUpdate(BaseModel):
    address: Optional[str] = None
    account_number: Optional[str] = None
    contact_details: Optional[str] = None

class AssignInstaller(BaseModel):
    installer_id: int

class ChangeStatus(BaseModel):
    status: OrderStatus

class CommentCreate(BaseModel):
    text: str

class CommentOut(BaseModel):
    id: int
    text: str
    created_at: datetime

    class Config:
        orm_mode = True

class OrderOut(BaseModel):
    id: int
    address: str
    account_number: str
    contact_details: str
    status: OrderStatus
    installer_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    comments: List[CommentOut] = []

    class Config:
        orm_mode = True

# Dependency to get DB session
def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()

@router.post("/", response_model=OrderOut)
def create_order(order: OrderCreate, db: Session = Depends(get_db), user=Depends(require_role([UserRole.ADMINISTRATOR, UserRole.DISPATCHER]))):
    db_order = Order(
        address=order.address,
        account_number=order.account_number,
        contact_details=order.contact_details,
        status=OrderStatus.IN_PROGRESS,
        created_by_id=user.id,
        updated_by_id=user.id
    )
    db.add(db_order)
    db.commit()
    # Create order history record
    from models import OrderHistory, OrderHistoryAction
    history = OrderHistory(
        order_id=db_order.id,
        user_id=user.id,
        action_type=OrderHistoryAction.CREATE,
        action_details=f"Order created with address: {order.address}"
    )
    db.add(history)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    orders = db.query(Order).all()
    return orders

@router.get("/my", response_model=List[OrderOut])
def list_my_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    me_as_installer = db.query(Installer).filter(Installer.user_id == user.id).one_or_none()

    if me_as_installer is None:
        return []

    orders = db.query(Order).filter(Order.installer_id == me_as_installer.id).all()

    return orders

@router.put("/{order_id}", response_model=OrderOut)
def update_order(order_id: int, order_update: OrderUpdate, db: Session = Depends(get_db), user=Depends(require_role([UserRole.ADMINISTRATOR, UserRole.DISPATCHER]))):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    for var, value in vars(order_update).items():
        if value is not None:
            setattr(db_order, var, value)
    db_order.updated_by_id = user.id
    # Create order history record
    from models import OrderHistory, OrderHistoryAction
    history = OrderHistory(
        order_id=order_id,
        user_id=user.id,
        action_type=OrderHistoryAction.UPDATE,
        action_details=f"Order updated: {order_update.dict(exclude_unset=True)}"
    )
    db.add(history)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.post("/{order_id}/assign_installer", response_model=OrderOut)
def assign_installer(order_id: int, assign: AssignInstaller, db: Session = Depends(get_db), user=Depends(require_role([UserRole.ADMINISTRATOR]))):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    db_installer = db.query(Installer).filter(Installer.id == assign.installer_id).first()
    if not db_installer:
        raise HTTPException(status_code=404, detail="Installer not found")
    db_order.installer = db_installer
    # Create order history record
    from models import OrderHistory, OrderHistoryAction
    history = OrderHistory(
        order_id=order_id,
        user_id=user.id,
        action_type=OrderHistoryAction.ASSIGN_INSTALLER,
        action_details=f"Assigned installer ID: {assign.installer_id}"
    )
    db.add(history)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.post("/{order_id}/change_status", response_model=OrderOut)
def change_status(order_id: int, status_change: ChangeStatus, db: Session = Depends(get_db), user=Depends(require_role([UserRole.INSTALLER]))):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    db_order.status = status_change.status
    # Create order history record
    from models import OrderHistory, OrderHistoryAction
    history = OrderHistory(
        order_id=order_id,
        user_id=user.id,
        action_type=OrderHistoryAction.CHANGE_STATUS,
        action_details=f"Changed status to: {status_change.status.value}"
    )
    db.add(history)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.post("/{order_id}/comments", response_model=CommentOut)
def add_comment(order_id: int, comment: CommentCreate, db: Session = Depends(get_db), user=Depends(require_role([UserRole.INSTALLER, UserRole.DISPATCHER, UserRole.ADMINISTRATOR]))):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    db_comment = Comment(order_id=order_id, text=comment.text)
    db.add(db_comment)
    db.commit()
    # Create order history record
    from models import OrderHistory, OrderHistoryAction
    history = OrderHistory(
        order_id=order_id,
        user_id=user.id,
        action_type=OrderHistoryAction.ADD_COMMENT,
        action_details=f"Added comment ID: {db_comment.id}"
    )
    db.add(history)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.get("/{order_id}/comments", response_model=List[CommentOut])
def list_comments(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db.query(Comment).filter(Comment.order_id == order_id).all()
