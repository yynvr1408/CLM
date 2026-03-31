"""Security utilities for authentication, authorization, and RBAC."""
import re
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import logging

# --- Python 3.13 + passlib monkeypatch ---
import passlib.utils.handlers
if not hasattr(passlib.utils.handlers, "HasRawParameters"):
    class _HasRawParameters:
        pass
    passlib.utils.handlers.HasRawParameters = _HasRawParameters

# Legacy passlib might fail to detect bcrypt version or handle bcrypt 4.0+
try:
    import bcrypt
    import passlib.handlers.bcrypt
    # Force passlib to use the installed bcrypt with correct settings
except ImportError:
    pass
# -----------------------------------------

from passlib.context import CryptContext
import jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ═══════════════════════════════════════════════════════════════
# Password Utilities
# ═══════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets complexity requirements.
    Returns (is_valid, error_message).
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"

    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':\"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"

    return True, ""


# ═══════════════════════════════════════════════════════════════
# JWT Token Utilities
# ═══════════════════════════════════════════════════════════════

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access"
) -> str:
    """Create JWT access token with a unique JTI."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        if token_type == "access":
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

    to_encode.update({
        "exp": expire,
        "type": token_type,
        "jti": str(uuid.uuid4()),  # unique token ID for blocklist
        "iat": datetime.now(timezone.utc),
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_token_from_request(credentials) -> str:
    """Extract token from request credentials."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return credentials.credentials


# ═══════════════════════════════════════════════════════════════
# RBAC Permission Checking
# ═══════════════════════════════════════════════════════════════

def check_permissions(user_permissions: list, required_permissions: list) -> bool:
    """Check if user has all required permissions."""
    user_perms = set(user_permissions)
    return all(p in user_perms for p in required_permissions)


def has_any_permission(user_permissions: list, required_permissions: list) -> bool:
    """Check if user has at least one of the required permissions."""
    user_perms = set(user_permissions)
    return any(p in user_perms for p in required_permissions)


# ═══════════════════════════════════════════════════════════════
# API Key Hashing
# ═══════════════════════════════════════════════════════════════

def generate_api_key() -> tuple[str, str, str]:
    """Generate API key, returns (raw_key, key_hash, key_prefix)."""
    raw_key = f"clm_{uuid.uuid4().hex}{uuid.uuid4().hex[:16]}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]
    return raw_key, key_hash, key_prefix


def hash_api_key(raw_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════
# Audit Trail Hashing (tamper-proof chain)
# ═══════════════════════════════════════════════════════════════

def compute_audit_hash(
    action: str,
    user_id: int,
    resource_type: str,
    timestamp: str,
    previous_hash: str = ""
) -> str:
    """Compute SHA-256 hash for audit log entry."""
    data = f"{action}|{user_id}|{resource_type}|{timestamp}|{previous_hash}"
    return hashlib.sha256(data.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════
# Input Sanitization
# ═══════════════════════════════════════════════════════════════

def sanitize_search_input(query: str) -> str:
    """Sanitize search input to prevent wildcard abuse."""
    # Escape special SQL LIKE characters
    query = query.replace('%', '\\%').replace('_', '\\_')
    # Limit length
    return query[:200]
