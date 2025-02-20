# File: database/models.py
from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    proof_threshold = Column(Integer, default=100)
    total_proofs = Column(Integer, default=0)
    successful_proofs = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Relationship with Request
    requests = relationship("Request", back_populates="user", cascade="all, delete-orphan")

class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_type = Column(String, nullable=False)  # ResNet-18 or ResNet-34
    image_path = Column(String, nullable=False)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    proof_generated = Column(Boolean, default=False)
    proof_verified = Column(Boolean, nullable=True)
    
    # Relationship with User
    user = relationship("User", back_populates="requests")
