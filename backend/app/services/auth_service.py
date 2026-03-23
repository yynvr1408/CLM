"""Authentication service."""
from sqlalchemy.orm import Session
from app.models.models import User, Role
from app.schemas.schemas import UserCreate
from app.core.security import hash_password, verify_password, create_access_token
from fastapi import HTTPException, status
from datetime import timedelta


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """Register a new user."""
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        # Get default role (user)
        default_role = db.query(Role).filter(Role.name == "user").first()
        if not default_role:
            # Create default role if doesn't exist
            default_role = Role(
                name="user",
                description="Standard user role",
                permissions={"read_contracts": True}
            )
            db.add(default_role)
            db.commit()
        
        # Create user
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name or "",
            hashed_password=hashed_password,
            role_id=default_role.id
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Authenticate user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """Get user by email."""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    
    @staticmethod
    def create_tokens(user: User) -> dict:
        """Create access and refresh tokens for user."""
        access_token_expires = timedelta(
            minutes=30  # 30 minutes
        )
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role_id": user.role_id},
            expires_delta=access_token_expires,
            token_type="access"
        )
        
        refresh_token = create_access_token(
            data={"sub": str(user.id), "type": "refresh"},
            token_type="refresh"
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800  # 30 minutes in seconds
        }
