"""SLA and renewal API endpoints with RBAC."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import RenewalCreate, RenewalResponse, RenewalUpdate
from app.services.sla_service import SLAService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user, require_permission

router = APIRouter(prefix="/renewals", tags=["renewals"])


@router.post("", response_model=RenewalResponse, status_code=201)
def create_renewal(
    contract_id: int,
    renewal_data: RenewalCreate,
    current_user: User = require_permission("contracts:update"),
    db: Session = Depends(get_db)
):
    """Create renewal record for contract."""
    return SLAService.create_renewal(db, contract_id, renewal_data)


@router.get("/contract/{contract_id}", response_model=dict)
def get_contract_renewals(
    contract_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = require_permission("contracts:read"),
    db: Session = Depends(get_db)
):
    """Get renewals for a contract."""
    renewals, total = SLAService.get_contract_renewals(db, contract_id, skip, limit)
    return {
        "total": total, "skip": skip, "limit": limit,
        "items": [RenewalResponse.model_validate(r) for r in renewals]
    }


@router.get("/upcoming", response_model=dict)
def get_upcoming_renewals(
    days_ahead: int = Query(30, ge=1, le=365),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = require_permission("contracts:read"),
    db: Session = Depends(get_db)
):
    """Get upcoming renewals."""
    renewals, total = SLAService.get_upcoming_renewals(db, days_ahead, skip, limit)
    return {
        "total": total, "skip": skip, "limit": limit, "days_ahead": days_ahead,
        "items": [RenewalResponse.model_validate(r) for r in renewals]
    }


@router.get("/overdue", response_model=dict)
def get_overdue_renewals(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = require_permission("contracts:read"),
    db: Session = Depends(get_db)
):
    """Get overdue renewals."""
    renewals, total = SLAService.get_overdue_renewals(db, skip, limit)
    return {
        "total": total, "skip": skip, "limit": limit,
        "items": [RenewalResponse.model_validate(r) for r in renewals]
    }


@router.post("/{renewal_id}/renew", response_model=RenewalResponse)
def mark_renewed(
    renewal_id: int,
    current_user: User = require_permission("contracts:update"),
    db: Session = Depends(get_db)
):
    """Mark renewal as completed."""
    return SLAService.mark_renewal_renewed(db, renewal_id, current_user.id)


@router.post("/{renewal_id}/notify", response_model=RenewalResponse)
def mark_notified(
    renewal_id: int,
    current_user: User = require_permission("contracts:update"),
    db: Session = Depends(get_db)
):
    """Mark renewal as notified."""
    return SLAService.mark_renewal_notified(db, renewal_id)


@router.patch("/{renewal_id}", response_model=RenewalResponse)
def update_renewal(
    renewal_id: int,
    renewal_data: RenewalUpdate,
    current_user: User = require_permission("contracts:update"),
    db: Session = Depends(get_db)
):
    """Update renewal status."""
    return SLAService.update_renewal(db, renewal_id, renewal_data)


@router.get("/{renewal_id}", response_model=RenewalResponse)
def get_renewal(
    renewal_id: int,
    current_user: User = require_permission("contracts:read"),
    db: Session = Depends(get_db)
):
    """Get renewal details."""
    return SLAService.get_renewal(db, renewal_id)
