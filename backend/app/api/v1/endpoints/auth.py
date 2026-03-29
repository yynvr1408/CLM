"""Authentication API endpoints with RBAC."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import (
    UserCreate, UserResponse, LoginRequest, TokenResponse,
    PasswordChangeRequest, UserAdminUpdate, RoleCreate, RoleUpdate, RoleResponse,
)
from app.services.auth_service import AuthService
from app.core.security import decode_token, security, get_token_from_request, check_permissions
from app.models.models import User, Role

router = APIRouter(prefix="/auth", tags=["authentication"])


# ═══════════════════════════════════════════════════════════════
# Current User Dependency (with token blocklist check)
# ═══════════════════════════════════════════════════════════════

def get_current_user(
    credentials=Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user with blocklist check."""
    token = get_token_from_request(credentials)
    payload = decode_token(token)

    # Check token blocklist
    jti = payload.get("jti")
    if jti and AuthService.is_token_blocklisted(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )

    user_id = int(payload.get("sub"))
    user = AuthService.get_user_by_id(db, user_id)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    return user


# ═══════════════════════════════════════════════════════════════
# RBAC Permission Dependency
# ═══════════════════════════════════════════════════════════════

def require_permission(*required_permissions: str):
    """FastAPI dependency factory that checks user has required permissions."""
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        # Superusers bypass permission checks
        if current_user.is_superuser:
            return current_user

        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        user_permissions = role.permissions if (role and isinstance(role.permissions, list)) else []

        if not check_permissions(user_permissions, list(required_permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(required_permissions)}"
            )
        return current_user

    return Depends(dependency)


def get_user_permissions(user: User, db: Session) -> list:
    """Get user's permission list."""
    if user.is_superuser:
        from app.models.models import ALL_PERMISSIONS
        return ALL_PERMISSIONS

    role = db.query(Role).filter(Role.id == user.role_id).first()
    return role.permissions if (role and isinstance(role.permissions, list)) else []


# ═══════════════════════════════════════════════════════════════
# Auth Endpoints
# ═══════════════════════════════════════════════════════════════

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user (requires admin approval)."""
    user = AuthService.register_user(db, user_data)
    permissions = get_user_permissions(user, db)
    role = db.query(Role).filter(Role.id == user.role_id).first()

    response = UserResponse.model_validate(user)
    response.permissions = permissions
    response.role_name = role.name if role else ""
    return response


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Login with email and password (with account lockout)."""
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)

    tokens = AuthService.create_tokens(user)
    return tokens


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user info with permissions."""
    permissions = get_user_permissions(current_user, db)
    role = db.query(Role).filter(Role.id == current_user.role_id).first()

    response = UserResponse.model_validate(current_user)
    response.permissions = permissions
    response.role_name = role.name if role else ""
    return response


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    credentials=Depends(security),
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

    # Check blocklist
    jti = payload.get("jti")
    if jti and AuthService.is_token_blocklisted(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )

    user_id = int(payload.get("sub"))
    user = AuthService.get_user_by_id(db, user_id)

    tokens = AuthService.create_tokens(user)
    return tokens


@router.post("/logout")
def logout(
    credentials=Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout and revoke token."""
    token = get_token_from_request(credentials)
    AuthService.revoke_token(db, token, current_user.id)
    return {"message": "Logged out successfully"}


@router.post("/change-password")
def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change current user's password."""
    AuthService.change_password(
        db, current_user, password_data.current_password, password_data.new_password
    )
    return {"message": "Password changed successfully"}


# ═══════════════════════════════════════════════════════════════
# Admin User Management
# ═══════════════════════════════════════════════════════════════

@router.get("/users", response_model=dict)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_approved: bool = Query(None),
    is_active: bool = Query(None),
    role_id: int = Query(None),
    current_user: User = require_permission("users:manage"),
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    users, total = AuthService.list_users(
        db, skip=skip, limit=limit,
        is_approved=is_approved, is_active=is_active, role_id=role_id,
    )

    items = []
    for u in users:
        perms = get_user_permissions(u, db)
        role = db.query(Role).filter(Role.id == u.role_id).first()
        resp = UserResponse.model_validate(u)
        resp.permissions = perms
        resp.role_name = role.name if role else ""
        items.append(resp)

    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.post("/users/{user_id}/approve", response_model=UserResponse)
def approve_user(
    user_id: int,
    current_user: User = require_permission("users:manage"),
    db: Session = Depends(get_db),
):
    """Approve a pending user registration."""
    user = AuthService.approve_user(db, user_id)
    response = UserResponse.model_validate(user)
    response.permissions = get_user_permissions(user, db)
    return response


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    current_user: User = require_permission("users:manage"),
    db: Session = Depends(get_db),
):
    """Deactivate a user account."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user = AuthService.deactivate_user(db, user_id)
    response = UserResponse.model_validate(user)
    response.permissions = get_user_permissions(user, db)
    return response


@router.post("/users/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    current_user: User = require_permission("users:manage"),
    db: Session = Depends(get_db),
):
    """Activate a user account."""
    user = AuthService.get_user_by_id(db, user_id)
    user.is_active = True
    user.is_approved = True
    db.commit()
    db.refresh(user)
    response = UserResponse.model_validate(user)
    response.permissions = get_user_permissions(user, db)
    return response


@router.post("/users/{user_id}/unlock", response_model=UserResponse)
def unlock_user(
    user_id: int,
    current_user: User = require_permission("users:manage"),
    db: Session = Depends(get_db),
):
    """Unlock a locked user account."""
    user = AuthService.unlock_user(db, user_id)
    response = UserResponse.model_validate(user)
    response.permissions = get_user_permissions(user, db)
    return response


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_id: int = Query(...),
    current_user: User = require_permission("users:manage"),
    db: Session = Depends(get_db),
):
    """Update a user's role."""
    user = AuthService.update_user_role(db, user_id, role_id)
    response = UserResponse.model_validate(user)
    response.permissions = get_user_permissions(user, db)
    role = db.query(Role).filter(Role.id == user.role_id).first()
    response.role_name = role.name if role else ""
    return response


# ═══════════════════════════════════════════════════════════════
# Role Management
# ═══════════════════════════════════════════════════════════════

@router.get("/roles", response_model=dict)
def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all roles."""
    roles = db.query(Role).order_by(Role.name).all()
    return {
        "items": [RoleResponse.model_validate(r) for r in roles],
        "total": len(roles),
    }


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    role_data: RoleCreate,
    current_user: User = require_permission("roles:manage"),
    db: Session = Depends(get_db),
):
    """Create a new role."""
    existing = db.query(Role).filter(Role.name == role_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role name already exists")

    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
        is_system_role=False,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.patch("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = require_permission("roles:manage"),
    db: Session = Depends(get_db),
):
    """Update a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system_role and role_data.name and role_data.name != role.name:
        raise HTTPException(status_code=400, detail="Cannot rename system roles")

    for field, value in role_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(role, field, value)

    db.commit()
    db.refresh(role)
    return role


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    current_user: User = require_permission("roles:manage"),
    db: Session = Depends(get_db),
):
    """Delete a role (only non-system roles)."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system_role:
        raise HTTPException(status_code=400, detail="Cannot delete system roles")

    # Check if any users use this role
    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete role — {user_count} users are assigned to it")

    db.delete(role)
    db.commit()


@router.get("/permissions")
def list_all_permissions(
    current_user: User = Depends(get_current_user),
):
    """List all available permissions."""
    from app.models.models import ALL_PERMISSIONS
    return {"permissions": ALL_PERMISSIONS}
