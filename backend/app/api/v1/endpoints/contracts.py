"""Contract management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.schemas import (
    ContractCreate, ContractResponse, ContractUpdate, ContractDetailResponse
)
from app.services.contract_service import ContractService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_data: ContractCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new contract."""
    contract = ContractService.create_contract(db, current_user.id, contract_data)
    return contract


@router.get("", response_model=dict)
def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    search: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List contracts with pagination and filtering."""
    contracts, total = ContractService.list_contracts(
        db,
        skip=skip,
        limit=limit,
        status=status,
        owner_id=None if current_user.is_superuser else current_user.id,
        search=search
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get contract details."""
    contract = ContractService.get_contract(db, contract_id)
    
    # Check authorization
    if not current_user.is_superuser and contract.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this contract"
        )
    
    return contract


@router.patch("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    change_summary: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update contract."""
    contract = ContractService.get_contract(db, contract_id)
    
    # Check authorization
    if contract.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this contract"
        )
    
    updated_contract = ContractService.update_contract(
        db,
        contract_id,
        contract_data,
        current_user.id,
        change_summary or "Updated contract"
    )
    
    return updated_contract


@router.post("/{contract_id}/submit")
def submit_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit contract for approval."""
    contract = ContractService.get_contract(db, contract_id)
    
    if contract.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    contract = ContractService.submit_contract(db, contract_id, current_user.id)
    return ContractResponse.model_validate(contract)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete contract."""
    contract = ContractService.get_contract(db, contract_id)
    
    if contract.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    ContractService.delete_contract(db, contract_id, current_user.id)
