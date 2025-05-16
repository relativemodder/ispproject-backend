from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from db import Base

class OrderStatus(PyEnum):
    IN_PROGRESS = "in_progress"
    NEEDS_REWORK = "needs_rework"
    COMPLETED = "completed"

class OrderHistoryAction(PyEnum):
    CREATE = "create"
    UPDATE = "update"
    ASSIGN_INSTALLER = "assign_installer"
    CHANGE_STATUS = "change_status"
    ADD_COMMENT = "add_comment"

class OrderHistory(Base):
    __tablename__ = "order_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(Enum(OrderHistoryAction), nullable=False)
    action_details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order")
    user = relationship("User")

class UserRole(PyEnum):
    ADMINISTRATOR = "administrator"
    DISPATCHER = "dispatcher"
    INSTALLER = "installer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    installer = relationship("Installer", back_populates="user", uselist=False)

class Installer(Base):
    __tablename__ = "installers"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_info = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    user = relationship("User", back_populates="installer", uselist=False)

    orders = relationship("Order", back_populates="installer")

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tokens")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    contact_details = Column(String, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.IN_PROGRESS, nullable=False)
    installer_id = Column(Integer, ForeignKey("installers.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    installer = relationship("Installer", back_populates="orders")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    comments = relationship("Comment", back_populates="order", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="comments")
