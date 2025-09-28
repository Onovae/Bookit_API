from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import timedelta
from typing import Optional

from app.models.user import User, UserRole
from app.schemas.auth import UserLogin, UserRegister, TokenResponse
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from app.config.settings import settings

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserRegister) -> User:
        # Check if user exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            role=UserRole.USER
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        user = self.db.query(User).filter(User.email == login_data.email).first()
        if not user:
            return None
        
        if not verify_password(login_data.password, user.password_hash):
            return None
        
        return user

    def create_tokens(self, user: User) -> TokenResponse:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        username = verify_token(refresh_token)
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = self.db.query(User).filter(User.email == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return self.create_tokens(user)