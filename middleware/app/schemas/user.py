# middleware/app/schemas/user.py
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    proof_threshold: int
    total_proofs: int
    successful_proofs: int
    success_rate: float

    class Config:
        orm_mode = True