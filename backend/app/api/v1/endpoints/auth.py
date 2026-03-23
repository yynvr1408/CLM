"""Authentication API endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import (
    UserCreate, UserResponse, LoginRequest, TokenResponse
)
from app.services.auth_service import AuthService
from app.core.security import decode_token, security, get_token_from_request
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_current_user(
    credentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    token = get_token_from_request(credentials)
    payload = decode_token(token)
    
    user_id = int(payload.get("sub"))
    user = AuthService.get_user_by_id(db, user_id)
    
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    user = AuthService.register_user(db, user_data)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Login with email and password."""
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    tokens = AuthService.create_tokens(user)
    return tokens


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    credentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    token = get_token_from_request(credentials)
    payload = decode_token(token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = int(payload.get("sub"))
    user = AuthService.get_user_by_id(db, user_id)
    
    tokens = AuthService.create_tokens(user)
    return tokens


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should delete tokens)."""
    return {"message": "Logged out successfully"}
