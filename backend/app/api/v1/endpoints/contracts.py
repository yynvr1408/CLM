"""Contract management API endpoints with RBAC."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.schemas import (
    ContractCreate, ContractResponse, ContractUpdate, ContractDetailResponse,
    BulkStatusUpdate, BulkDeleteRequest, TagResponse, DashboardStats,
)
from app.services.contract_service import ContractService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user, require_permission

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_data: ContractCreate,
    current_user: User = require_permission("contracts:create"),
    db: Session = Depends(get_db)
):
    """Create a new contract."""
    contract = ContractService.create_contract(
        db, current_user.id, contract_data,
        organization_id=current_user.organization_id,
    )
    return contract


@router.get("", response_model=dict)
def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    search: str = Query(None),
    current_user: User = require_permission("contracts:read"),
    db: Session = Depends(get_db),
):
    """List contracts with pagination and filtering."""
    # Users with read_all can see all org contracts; others see only their own
    from app.models.models import Role
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    user_perms = role.permissions if (role and isinstance(role.permissions, list)) else []

    owner_id = None
    if not current_user.is_superuser and "contracts:read_all" not in user_perms:
        owner_id = current_user.id

    contracts, total = ContractService.list_contracts(
        db,
        skip=skip,
        limit=limit,
        status=status,
        owner_id=owner_id,
        organization_id=current_user.organization_id,
        search=search,
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [ContractResponse.model_validate(c) for c in contracts]
    }


@router.get("/stats", response_model=DashboardStats)
def get_contract_stats(
    current_user: User = require_permission("contracts:read"),
    db: Session = Depends(get_db),
):
    """Get contract dashboard statistics."""
    from app.models.models import Role
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    user_perms = role.permissions if (role and isinstance(role.permissions, list)) else []

    owner_id = None
    if not current_user.is_superuser and "contracts:read_all" not in user_perms:
        owner_id = current_user.id

    stats = ContractService.get_dashboard_stats(
        db, owner_id=owner_id,
        organization_id=current_user.organization_id,
    )
    return DashboardStats(**stats)


@router.get("/expiring", response_model=dict)
def get_expiring_contracts(
    days_ahead: int = Query(30, ge=1, le=365),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = require_permission("contracts:read"),
    db: Session = Depends(get_db),
):
    """Get contracts expiring within N days."""
    contracts, total = ContractService.get_expiring_contracts(
        db, days_ahead=days_ahead, skip=skip, limit=limit,
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [ContractResponse.model_validate(c) for c in contracts]
    }


@router.get("/{contract_id}", response_model=ContractDetailResponse)
def get_contract(
    contract_id: int,
    current_user: User = require_permission("contracts:read"),
    db: Session = Depends(get_db),
):
    """Get contract details."""
    contract = ContractService.get_contract(db, contract_id)

    # Check authorization
    from app.models.models import Role
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    user_perms = role.permissions if (role and isinstance(role.permissions, list)) else []

    if (not current_user.is_superuser
        and "contracts:read_all" not in user_perms
        and contract.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this contract"
        )

    # Build response with clauses and tags
    clause_list = []
    for cc in contract.clauses:
        if cc.clause:
            from app.schemas.schemas import ClauseResponse
            clause_list.append(ClauseResponse.model_validate(cc.clause))

    tag_list = []
    for ct in contract.tags:
        if ct.tag:
            tag_list.append(TagResponse.model_validate(ct.tag))

    # Construct response manually to avoid Pydantic/SQLAlchemy relationship name conflicts
    base_data = ContractResponse.model_validate(contract).model_dump()
    resp = ContractDetailResponse(
        **base_data,
        clauses=clause_list,
        tags=tag_list
    )
    return resp


@router.patch("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    change_summary: str = Query(None),
    current_user: User = require_permission("contracts:update"),
    db: Session = Depends(get_db),
):
    """Update contract."""
    contract = ContractService.get_contract(db, contract_id)

    from app.models.models import Role
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    user_perms = role.permissions if (role and isinstance(role.permissions, list)) else []

    if (not current_user.is_superuser
        and "contracts:update_all" not in user_perms
        and contract.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this contract"
        )

    updated = ContractService.update_contract(
        db, contract_id, contract_data, current_user.id,
        change_summary or "Updated contract"
    )
    return updated


@router.post("/{contract_id}/submit")
def submit_contract(
    contract_id: int,
    current_user: User = require_permission("contracts:submit"),
    db: Session = Depends(get_db),
):
    """Submit contract for approval."""
    contract = ContractService.get_contract(db, contract_id)

    from app.models.models import Role
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    user_perms = role.permissions if (role and isinstance(role.permissions, list)) else []

    if (not current_user.is_superuser
        and "contracts:update_all" not in user_perms
        and contract.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    contract = ContractService.submit_contract(db, contract_id, current_user.id)
    return ContractResponse.model_validate(contract)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: int,
    current_user: User = require_permission("contracts:delete"),
    db: Session = Depends(get_db),
):
    """Soft delete contract."""
    contract = ContractService.get_contract(db, contract_id)

    from app.models.models import Role
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    user_perms = role.permissions if (role and isinstance(role.permissions, list)) else []

    if (not current_user.is_superuser
        and "contracts:delete_all" not in user_perms
        and contract.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    ContractService.delete_contract(db, contract_id, current_user.id)


@router.post("/{contract_id}/restore", response_model=ContractResponse)
def restore_contract(
    contract_id: int,
    current_user: User = require_permission("contracts:delete"),
    db: Session = Depends(get_db),
):
    """Restore a soft-deleted contract."""
    contract = ContractService.restore_contract(db, contract_id, current_user.id)
    return contract


@router.post("/bulk/status", response_model=dict)
def bulk_update_status(
    data: BulkStatusUpdate,
    current_user: User = require_permission("contracts:update_all"),
    db: Session = Depends(get_db),
):
    """Bulk update contract statuses."""
    updated = ContractService.bulk_update_status(db, data.contract_ids, data.new_status, current_user.id)
    return {"updated": updated}


@router.post("/bulk/delete", response_model=dict)
def bulk_delete(
    data: BulkDeleteRequest,
    current_user: User = require_permission("contracts:delete_all"),
    db: Session = Depends(get_db),
):
    """Bulk soft-delete contracts."""
    deleted = ContractService.bulk_delete(db, data.contract_ids, current_user.id)
    return {"deleted": deleted}
