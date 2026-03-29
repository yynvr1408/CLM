"""Audit logging API endpoints with RBAC."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database.session import get_db
from app.schemas.schemas import AuditLogResponse
from app.services.audit_service import AuditService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user, require_permission

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=dict)
def get_audit_logs(
    user_id: int = Query(None),
    contract_id: int = Query(None),
    action: str = Query(None),
    resource_type: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = require_permission("audit:view"),
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering (admin sees all, users see own)."""
    if not current_user.is_superuser:
        # Non-admin users can only see their own activity
        from app.models.models import Role
        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        user_perms = role.permissions if (role and isinstance(role.permissions, list)) else []
        if "audit:view" in user_perms and "users:manage" not in user_perms:
            user_id = current_user.id

    logs, total = AuditService.get_audit_logs(
        db, user_id=user_id, contract_id=contract_id,
        action=action, resource_type=resource_type,
        skip=skip, limit=limit
    )
    return {
        "total": total, "skip": skip, "limit": limit,
        "items": [AuditLogResponse.model_validate(log) for log in logs]
    }


@router.get("/trail/{contract_id}", response_model=dict)
def get_contract_audit_trail(
    contract_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = require_permission("audit:view"),
    db: Session = Depends(get_db)
):
    """Get complete audit trail for a contract."""
    logs, total = AuditService.get_contract_audit_trail(
        db, contract_id=contract_id, skip=skip, limit=limit
    )
    return {
        "total": total, "skip": skip, "limit": limit, "contract_id": contract_id,
        "items": [AuditLogResponse.model_validate(log) for log in logs]
    }


@router.get("/user/activity", response_model=dict)
def get_user_activity(
    days: int = Query(30, ge=1, le=365),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's activity."""
    logs, total = AuditService.get_user_activity(
        db, user_id=current_user.id, days=days, skip=skip, limit=limit
    )
    return {
        "total": total, "skip": skip, "limit": limit, "days": days,
        "items": [AuditLogResponse.model_validate(log) for log in logs]
    }


@router.get("/export/{contract_id}")
def export_audit_trail(
    contract_id: int,
    current_user: User = require_permission("audit:export"),
    db: Session = Depends(get_db)
):
    """Export contract audit trail as JSON."""
    audit_trail = AuditService.export_audit_trail(db, contract_id)
    return {
        "contract_id": contract_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "records": audit_trail
    }
