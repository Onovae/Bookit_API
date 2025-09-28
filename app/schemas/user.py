from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole

# Base User Schema
class UserBase(BaseModel):
    name: str
    email: EmailStr

# User Creation Schema (for registration)
class UserCreate(UserBase):
    password: str

# User Response Schema
class UserResponse(UserBase):
    id: UUID
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True

# User Update Schema
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

# Admin User Creation Schema
class AdminUserCreate(UserCreate):
    role: UserRole = UserRole.USER