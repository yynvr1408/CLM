"""Authentication service with account lockout, registration approval, token blocklist."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.models import User, Role, TokenBlocklist
from app.schemas.schemas import UserCreate
from app.core.security import (
    hash_password, verify_password, create_access_token,
    validate_password_strength, decode_token
)
from app.core.config import settings
from fastapi import HTTPException, status


class AuthService:
    """Service for authentication operations."""

    # ── Registration ──────────────────────────────────────────

    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """Register a new user (inactive until admin approves)."""
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )

        # Validate password strength
        is_valid, error_msg = validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Check email domain restriction
        if settings.ALLOWED_EMAIL_DOMAINS:
            domain = user_data.email.split('@')[1]
            if domain not in settings.ALLOWED_EMAIL_DOMAINS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration restricted to approved email domains"
                )

        # Get default role (viewer for new users)
        default_role = db.query(Role).filter(Role.name == "viewer").first()
        if not default_role:
            default_role = db.query(Role).filter(Role.name == "user").first()
        if not default_role:
            default_role = Role(
                name="viewer",
                description="Read-only access",
                permissions=["contracts:read", "clauses:read", "approvals:view",
                            "templates:read", "tags:read", "comments:read"],
            )
            db.add(default_role)
            db.commit()

        # Create user
        requires_approval = settings.REGISTRATION_REQUIRES_APPROVAL
        hashed_pw = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name or "",
            hashed_password=hashed_pw,
            role_id=default_role.id,
            is_active=not requires_approval,  # active only if no approval needed
            is_approved=not requires_approval,
            password_changed_at=datetime.now(timezone.utc),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    # ── Authentication ────────────────────────────────────────

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Authenticate user with account lockout."""
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check account lockout
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = (user.locked_until - datetime.now(timezone.utc)).seconds // 60
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked. Try again in {remaining + 1} minutes."
            )

        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            # Lock account if max attempts exceeded
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.ACCOUNT_LOCKOUT_MINUTES
                )
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked for {settings.ACCOUNT_LOCKOUT_MINUTES} minutes due to too many failed attempts"
                )

            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if user is approved
        if not user.is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is pending admin approval"
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Contact administrator."
            )

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        return user

    # ── User Retrieval ────────────────────────────────────────

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

    # ── Token Management ──────────────────────────────────────

    @staticmethod
    def create_tokens(user: User) -> dict:
        """Create access and refresh tokens for user."""
        # Load role permissions
        role = user.role
        permissions = role.permissions if role and isinstance(role.permissions, list) else []

        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role_id": user.role_id,
            "role_name": role.name if role else "",
            "permissions": permissions,
            "is_superuser": user.is_superuser,
            "org_id": user.organization_id,
        }

        access_token = create_access_token(
            data=access_token_data,
            token_type="access"
        )

        refresh_token = create_access_token(
            data={"sub": str(user.id)},
            token_type="refresh"
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    # ── Logout / Token Revocation ─────────────────────────────

    @staticmethod
    def revoke_token(db: Session, token: str, user_id: int):
        """Add token to blocklist (revoke it)."""
        try:
            payload = decode_token(token)
        except Exception:
            return  # if token is already expired, no need to blocklist

        jti = payload.get("jti")
        if not jti:
            return

        # Check if already blocklisted
        existing = db.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).first()
        if existing:
            return

        blocked = TokenBlocklist(
            jti=jti,
            token_type=payload.get("type", "access"),
            user_id=user_id,
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
        db.add(blocked)
        db.commit()

    @staticmethod
    def is_token_blocklisted(db: Session, jti: str) -> bool:
        """Check if a token JTI is blocklisted."""
        return db.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).first() is not None

    # ── Password Change ───────────────────────────────────────

    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
        """Change user password."""
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    # ── Admin User Management ─────────────────────────────────

    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        is_approved: bool = None,
        is_active: bool = None,
        role_id: int = None,
    ) -> tuple:
        """List users with filtering (admin only)."""
        query = db.query(User)

        if is_approved is not None:
            query = query.filter(User.is_approved == is_approved)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if role_id is not None:
            query = query.filter(User.role_id == role_id)

        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        return users, total

    @staticmethod
    def approve_user(db: Session, user_id: int) -> User:
        """Approve a pending user registration."""
        user = AuthService.get_user_by_id(db, user_id)
        user.is_approved = True
        user.is_active = True
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> User:
        """Deactivate a user account."""
        user = AuthService.get_user_by_id(db, user_id)
        user.is_active = False
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user_role(db: Session, user_id: int, role_id: int) -> User:
        """Update user's role."""
        user = AuthService.get_user_by_id(db, user_id)
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        user.role_id = role_id
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def unlock_user(db: Session, user_id: int) -> User:
        """Unlock a locked user account."""
        user = AuthService.get_user_by_id(db, user_id)
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        db.refresh(user)
        return user
