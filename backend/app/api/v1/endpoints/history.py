"""History and Audit API endpoints."""
import csv
import io
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.schemas import AuditLogResponse, ClauseVersionResponse, IntegrityStatus, ContractVersionResponse
from app.models.models import User, AuditLog, ClauseVersion, ContractVersion
from app.services.audit_service import AuditService
from app.services.clause_service import ClauseService
from app.api.v1.endpoints.auth import get_current_user, require_permission, get_user_from_query_token
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


@router.get("/export")
def export_audit_logs(
    current_user: User = Depends(get_user_from_query_token),
    db: Session = Depends(get_db)
):
    """Export all audit logs to a CSV file."""
    # Manual permission check since we are bypassing require_permission dependency
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if not current_user.is_superuser:
        if not role or "audit:export" not in (role.permissions or []):
            raise HTTPException(status_code=403, detail="Insufficient permissions: audit:export required")
    logs = AuditService.get_all_audit_logs(db)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Timestamp", "User", "Action", "Resource Type", "Resource ID", "Changes", "IP Address"])
    
    for log in logs:
        user_name = log.user.full_name if log.user else f"User {log.user_id}"
        writer.writerow([
            log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            user_name,
            log.action,
            log.resource_type,
            log.resource_id or "-",
            json.dumps(log.changes) if log.changes else "-",
            log.ip_address or "-"
        ])
    
    output.seek(0)
    filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/contract/{contract_id}/versions", response_model=List[ContractVersionResponse])
def get_contract_versions(
    contract_id: int,
    current_user: User = require_permission("contracts:read"),
    db: Session = Depends(get_db)
):
    """Get version history for a contract."""
    from sqlalchemy.orm import joinedload
    versions = db.query(ContractVersion).options(joinedload(ContractVersion.contract)).filter(
        ContractVersion.contract_id == contract_id
    ).order_by(ContractVersion.version_number.desc()).all()
    
    resp = []
    for v in versions:
        item = ContractVersionResponse.model_validate(v)
        # Find user who created this version
        from app.models.models import User as UserInfo
        user = db.query(UserInfo).filter(UserInfo.id == v.created_by_id).first()
        if user:
            item.created_by_name = user.full_name
        resp.append(item)
        
    return resp
