"""History and Audit API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.schemas import AuditLogResponse, ClauseVersionResponse, IntegrityStatus
from app.models.models import User, AuditLog, ClauseVersion
from app.services.audit_service import AuditService
from app.services.clause_service import ClauseService
from app.api.v1.endpoints.auth import get_current_user, require_permission
from app.models.models import Role

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/contract/{contract_id}", response_model=List[AuditLogResponse])
def get_contract_history(
    contract_id: int,
    current_user: User = require_permission("audit:view"),
    db: Session = Depends(get_db)
):
    """Get audit trail for a specific contract."""
    # Strict role check
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    allowed_roles = ["super_admin", "admin", "contract_manager"]
    if not current_user.is_superuser and (not role or role.name not in allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only admins and contract managers can view history."
        )

    logs, _ = AuditService.get_contract_audit_trail(db, contract_id, limit=200)
    
    # Map with user info
    resp = []
    for log in logs:
        item = AuditLogResponse.model_validate(log)
        if log.user:
            item.user_full_name = log.user.full_name
        resp.append(item)
    return resp

@router.get("/clause/{clause_id}/versions", response_model=List[ClauseVersionResponse])
def get_clause_versions(
    clause_id: int,
    current_user: User = require_permission("templates:read"),
    db: Session = Depends(get_db)
):
    """Get version history for a clause."""
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    allowed_roles = ["super_admin", "admin", "contract_manager"]
    if not current_user.is_superuser and (not role or role.name not in allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only admins and contract managers can view version history."
        )

    versions = db.query(ClauseVersion).filter(
        ClauseVersion.clause_id == clause_id
    ).order_by(ClauseVersion.version_number.desc()).all()
    return versions

@router.post("/clause/{clause_id}/restore/{version_id}")
def restore_clause_version(
    clause_id: int,
    version_id: int,
    current_user: User = require_permission("templates:update"),
    db: Session = Depends(get_db)
):
    """Restore a clause to a previous version."""
    return ClauseService.restore_version(db, clause_id, version_id, current_user.id)

@router.get("/integrity", response_model=IntegrityStatus)
def check_audit_integrity(
    current_user: User = require_permission("audit:view"),
    db: Session = Depends(get_db)
):
    """Verify the integrity of the total audit log chain."""
    return AuditService.verify_chain(db)
