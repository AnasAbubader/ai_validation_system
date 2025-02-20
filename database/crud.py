# File: database/crud.py
from sqlalchemy.orm import Session
from typing import List, Optional
import random
from pathlib import Path
from .models import User, Request

# User operations
def create_user(db: Session, username: str, email: str, password_hash: str) -> User:
    """Create a new user"""
    user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def update_proof_threshold(db: Session, user_id: int, threshold: int) -> Optional[User]:
    """Update user's proof threshold"""
    user = get_user_by_id(db, user_id)
    if user:
        user.proof_threshold = threshold
        db.commit()
        db.refresh(user)
    return user

def update_proof_stats(db: Session, user_id: int, proof_verified: bool) -> Optional[User]:
    """Update user's proof statistics"""
    user = get_user_by_id(db, user_id)
    if user:
        user.total_proofs += 1
        if proof_verified:
            user.successful_proofs += 1
        user.success_rate = (user.successful_proofs / user.total_proofs) * 100
        db.commit()
        db.refresh(user)
    return user

# Request operations
def create_request(
    db: Session, 
    user_id: int, 
    model_type: str, 
    image_path: str,
    result: dict = None
) -> Request:
    """Create a new request record"""
    request = Request(
        user_id=user_id,
        model_type=model_type,
        image_path=image_path,
        result=result
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

def get_request_by_id(db: Session, request_id: int) -> Optional[Request]:
    """Get a specific request by its ID"""
    return db.query(Request).filter(Request.id == request_id).first()

def get_user_requests(db: Session, user_id: int, verified_only: bool = False) -> List[Request]:
    """Get all requests for a user"""
    query = db.query(Request).filter(Request.user_id == user_id)
    if verified_only:
        query = query.filter(Request.proof_verified == True)
    return query.all()

def get_user_request_paths(db: Session, user_id: int) -> List[str]:
    """Get all image paths for a user's unverified requests"""
    requests = (
        db.query(Request.image_path)
        .filter(Request.user_id == user_id)
        .filter(Request.proof_generated == False)
        .all()
    )
    return [request.image_path for request in requests]

def count_user_requests(db: Session, user_id: int) -> int:
    """Count total number of requests for a user"""
    return db.query(Request).filter(Request.user_id == user_id).count()

def get_random_unverified_request(db: Session, user_id: int) -> Optional[Request]:
    """Get a random unverified request that has an existing image file"""
    unverified_requests = (
        db.query(Request)
        .filter(Request.user_id == user_id)
        .filter(Request.proof_generated == False)
        .all()
    )
    
    # Filter requests to only those with existing image files
    valid_requests = [
        req for req in unverified_requests 
        if Path(req.image_path).exists()
    ]
    
    return random.choice(valid_requests) if valid_requests else None

def update_proof_status(
    db: Session, 
    request_id: int, 
    proof_generated: bool = True,
    proof_verified: Optional[bool] = None,
    verification_failed: bool = False
) -> Optional[Request]:
    """Update the proof status of a request"""
    request = get_request_by_id(db, request_id)
    if request:
        request.proof_generated = proof_generated
        if verification_failed:
            request.proof_verified = False
        elif proof_verified is not None:
            request.proof_verified = proof_verified
        db.commit()
        db.refresh(request)
    return request

def delete_user_requests(db: Session, user_id: int, delete_verified_only: bool = False) -> None:
    """
    Delete user requests from database
    
    Args:
        db: Database session
        user_id: ID of the user
        delete_verified_only: If True, only delete requests that have been verified
    """
    query = db.query(Request).filter(Request.user_id == user_id)
    if delete_verified_only:
        query = query.filter(Request.proof_generated == True)
    query.delete()
    db.commit()

def get_failed_verifications(db: Session, user_id: int) -> List[Request]:
    """Get all requests that failed verification"""
    return (
        db.query(Request)
        .filter(Request.user_id == user_id)
        .filter(Request.proof_generated == True)
        .filter(Request.proof_verified == False)
        .all()
    )

def get_pending_proof_requests(db: Session, user_id: int) -> List[Request]:
    """
    Get all requests that are awaiting proof generation
    
    Args:
        db: Database session
        user_id: ID of the user
    Returns:
        List of requests awaiting proof
    """
    return (
        db.query(Request)
        .filter(Request.user_id == user_id)
        .filter(Request.proof_generated == False)
        .all()
    )

def get_verification_stats(db: Session, user_id: int) -> dict:
    """
    Get detailed verification statistics for a user
    
    Args:
        db: Database session
        user_id: ID of the user
    Returns:
        Dictionary containing verification statistics
    """
    total_requests = count_user_requests(db, user_id)
    failed_verifications = len(get_failed_verifications(db, user_id))
    pending_proofs = len(get_pending_proof_requests(db, user_id))
    
    return {
        "total_requests": total_requests,
        "failed_verifications": failed_verifications,
        "pending_proofs": pending_proofs,
        "processed_requests": total_requests - pending_proofs
    }