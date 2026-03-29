"""Approval workflow API endpoints with RBAC."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import ApprovalCreate, ApprovalResponse
from app.services.workflow_service import WorkflowService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user, require_permission

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
def create_approval(
    contract_id: int,
    approval_data: ApprovalCreate,
    current_user: User = require_permission("approvals:assign"),
    db: Session = Depends(get_db)
):
    """Create approval request for contract."""
    return WorkflowService.create_approval(db, contract_id, approval_data)


@router.get("/contract/{contract_id}", response_model=dict)
def get_contract_approvals(
    contract_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = require_permission("approvals:view"),
    db: Session = Depends(get_db)
):
    """Get all approvals for a contract."""
    approvals, total = WorkflowService.get_contract_approvals(
        db, contract_id=contract_id, skip=skip, limit=limit
    )
    items = []
    for a in approvals:
        resp = ApprovalResponse.model_validate(a)
        if a.contract:
            resp.contract_title = a.contract.title
            resp.contract_number = a.contract.contract_number
        items.append(resp)

    return {
        "total": total, "skip": skip, "limit": limit, "contract_id": contract_id,
        "items": items
    }


@router.get("/pending", response_model=dict)
def get_pending_approvals(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending approvals for current user."""
    approvals, total = WorkflowService.get_pending_approvals_for_user(
        db, approver_id=current_user.id, skip=skip, limit=limit
    )
    items = []
    for a in approvals:
        resp = ApprovalResponse.model_validate(a)
        if a.contract:
            resp.contract_title = a.contract.title
            resp.contract_number = a.contract.contract_number
        items.append(resp)

    return {
        "total": total, "skip": skip, "limit": limit,
        "items": items
    }


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve_contract(
    approval_id: int,
    comments: str = Query(None),
    current_user: User = require_permission("approvals:approve"),
    db: Session = Depends(get_db)
):
    """Approve contract."""
    return WorkflowService.approve_contract(
        db, approval_id, current_user.id, comments=comments
    )


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject_contract(
    approval_id: int,
    comments: str = Query(...),
    current_user: User = require_permission("approvals:reject"),
    db: Session = Depends(get_db)
):
    """Reject contract."""
    return WorkflowService.reject_contract(
        db, approval_id, current_user.id, comments=comments
    )


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: int,
    current_user: User = require_permission("approvals:view"),
    db: Session = Depends(get_db)
):
    """Get approval details."""
    return WorkflowService.get_approval(db, approval_id)
