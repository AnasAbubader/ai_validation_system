# middleware/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database.base import get_db
from database.crud import create_user, get_user_by_username
from ..core.security import verify_password, create_access_token, get_password_hash
from datetime import timedelta
from ..core.config import settings
from ..schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(400, "Username already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    return user

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Incorrect username or password")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }