"""Contract management service."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from app.models.models import (
    Contract, ContractVersion, Clause, ContractClause, User,
    Approval, Renewal, AuditLog
)
from app.schemas.schemas import ContractCreate, ContractUpdate
from fastapi import HTTPException, status
from datetime import datetime
import uuid


class ContractService:
    """Service for contract operations."""
    
    @staticmethod
    def generate_contract_number() -> str:
        """Generate unique contract number."""
        return f"CNT-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    @staticmethod
    def create_contract(
        db: Session,
        owner_id: int,
        contract_data: ContractCreate
    ) -> Contract:
        """Create a new contract."""
        # Generate contract number
        contract_number = ContractService.generate_contract_number()
        
        # Create contract
        new_contract = Contract(
            contract_number=contract_number,
            title=contract_data.title,
            description=contract_data.description,
            owner_id=owner_id,
            contract_type=contract_data.contract_type,
            value=contract_data.value,
            currency=contract_data.currency,
            start_date=contract_data.start_date,
            end_date=contract_data.end_date,
            status="draft"
        )
        
        db.add(new_contract)
        db.flush()  # Get the ID without committing
        
        # Add clauses if provided
        if contract_data.clauses:
            for clause_link in contract_data.clauses:
                clause = db.query(Clause).filter(
                    Clause.id == clause_link.clause_id
                ).first()
                
                if clause:
                    contract_clause = ContractClause(
                        contract_id=new_contract.id,
                        clause_id=clause.id,
                        order=clause_link.order
                    )
                    db.add(contract_clause)
        
        # Create initial version
        version = ContractVersion(
            contract_id=new_contract.id,
            version_number=1,
            change_summary="Initial version",
            created_by_id=owner_id
        )
        db.add(version)
        
        db.commit()
        db.refresh(new_contract)
        
        return new_contract
    
    @staticmethod
    def get_contract(db: Session, contract_id: int) -> Contract:
        """Get contract by ID."""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        return contract
    
    @staticmethod
    def get_contract_by_number(db: Session, contract_number: str) -> Contract:
        """Get contract by contract number."""
        contract = db.query(Contract).filter(
            Contract.contract_number == contract_number
        ).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        return contract
    
    @staticmethod
    def update_contract(
        db: Session,
        contract_id: int,
        contract_data: ContractUpdate,
        user_id: int,
        change_summary: str = ""
    ) -> Contract:
        """Update contract and create new version."""
        contract = ContractService.get_contract(db, contract_id)
        
        # Store old values for audit
        changes = {}
        
        # Update fields
        for field, value in contract_data.dict(exclude_unset=True).items():
            if value is not None:
                old_value = getattr(contract, field, None)
                setattr(contract, field, value)
                changes[field] = {"old": old_value, "new": value}
        
        # Create new version
        latest_version = db.query(ContractVersion).filter(
            ContractVersion.contract_id == contract_id
        ).order_by(desc(ContractVersion.version_number)).first()
        
        next_version = (latest_version.version_number + 1) if latest_version else 2
        
        version = ContractVersion(
            contract_id=contract_id,
            version_number=next_version,
            change_summary=change_summary or "Updated contract",
            created_by_id=user_id
        )
        db.add(version)
        
        # Audit log
        audit = AuditLog(
            user_id=user_id,
            contract_id=contract_id,
            action="UPDATE",
            resource_type="contract",
            resource_id=contract_id,
            changes=changes
        )
        db.add(audit)
        
        db.commit()
        db.refresh(contract)
        
        return contract
    
    @staticmethod
    def list_contracts(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: str = None,
        owner_id: int = None,
        search: str = None
    ) -> tuple:
        """List contracts with filtering."""
        query = db.query(Contract)
        
        if status:
            query = query.filter(Contract.status == status)
        if owner_id:
            query = query.filter(Contract.owner_id == owner_id)
        if search:
            query = query.filter(
                or_(
                    Contract.title.ilike(f"%{search}%"),
                    Contract.contract_number.ilike(f"%{search}%"),
                    Contract.description.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        contracts = query.order_by(desc(Contract.created_at)).offset(skip).limit(limit).all()
        
        return contracts, total
    
    @staticmethod
    def submit_contract(db: Session, contract_id: int, user_id: int) -> Contract:
        """Submit contract for approval."""
        contract = ContractService.get_contract(db, contract_id)
        
        if contract.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit contract with status '{contract.status}'"
            )
        
        contract.status = "submitted"
        
        # Create audit log
        audit = AuditLog(
            user_id=user_id,
            contract_id=contract_id,
            action="SUBMIT",
            resource_type="contract",
            resource_id=contract_id
        )
        db.add(audit)
        
        db.commit()
        db.refresh(contract)
        
        return contract
    
    @staticmethod
    def delete_contract(db: Session, contract_id: int, user_id: int) -> None:
        """Delete contract (soft delete by marking as archived)."""
        contract = ContractService.get_contract(db, contract_id)
        
        # Audit log
        audit = AuditLog(
            user_id=user_id,
            contract_id=contract_id,
            action="DELETE",
            resource_type="contract",
            resource_id=contract_id
        )
        db.add(audit)
        
        db.delete(contract)
        db.commit()
