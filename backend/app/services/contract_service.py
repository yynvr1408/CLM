"""Contract management service with soft delete and org scoping."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.models.models import (
    Contract, ContractVersion, Clause, ContractClause, ContractTag,
    Tag, AuditLog, utcnow
)
from app.schemas.schemas import ContractCreate, ContractUpdate
from app.core.security import sanitize_search_input, compute_audit_hash
from fastapi import HTTPException, status
from datetime import datetime, timezone, date, timedelta
import uuid


class ContractService:
    """Service for contract operations."""

    @staticmethod
    def generate_contract_number() -> str:
        """Generate unique contract number."""
        return f"CNT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    @staticmethod
    def create_contract(
        db: Session,
        owner_id: int,
        contract_data: ContractCreate,
        organization_id: int = None,
    ) -> Contract:
        """Create a new contract."""
        contract_number = ContractService.generate_contract_number()

        new_contract = Contract(
            contract_number=contract_number,
            title=contract_data.title,
            description=contract_data.description,
            owner_id=owner_id,
            organization_id=organization_id,
            template_id=contract_data.template_id,
            contract_type=contract_data.contract_type,
            value=contract_data.value,
            currency=contract_data.currency,
            start_date=contract_data.start_date,
            end_date=contract_data.end_date,
            metadata_fields=contract_data.metadata_fields,
            status="draft"
        )

        db.add(new_contract)
        db.flush()

        # Add clauses
        if contract_data.clauses:
            for clause_link in contract_data.clauses:
                clause = db.query(Clause).filter(Clause.id == clause_link.clause_id).first()
                if clause:
                    contract_clause = ContractClause(
                        contract_id=new_contract.id,
                        clause_id=clause.id,
                        order=clause_link.order
                    )
                    db.add(contract_clause)

        # Add tags
        if contract_data.tag_ids:
            for tag_id in contract_data.tag_ids:
                tag = db.query(Tag).filter(Tag.id == tag_id).first()
                if tag:
                    contract_tag = ContractTag(
                        contract_id=new_contract.id,
                        tag_id=tag.id
                    )
                    db.add(contract_tag)

        # Create initial version
        version = ContractVersion(
            contract_id=new_contract.id,
            version_number=1,
            change_summary="Initial version",
            created_by_id=owner_id
        )
        db.add(version)

        # Audit log
        audit = AuditLog(
            user_id=owner_id,
            contract_id=new_contract.id,
            action="CREATE",
            resource_type="contract",
            resource_id=new_contract.id,
        )
        db.add(audit)

        db.commit()
        db.refresh(new_contract)

        return new_contract

    @staticmethod
    def get_contract(db: Session, contract_id: int) -> Contract:
        """Get contract by ID (excluding soft-deleted)."""
        contract = db.query(Contract).filter(
            Contract.id == contract_id,
            Contract.is_deleted == False
        ).first()

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
            Contract.contract_number == contract_number,
            Contract.is_deleted == False
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

        changes = {}
        for field, value in contract_data.model_dump(exclude_unset=True).items():
            if value is not None:
                old_value = getattr(contract, field, None)
                # Convert dates and datetimes to strings for JSON serialization
                old_str = str(old_value) if old_value is not None else None
                new_str = str(value) if value is not None else None
                setattr(contract, field, value)
                changes[field] = {"old": old_str, "new": new_str}

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
        organization_id: int = None,
        search: str = None,
        include_deleted: bool = False,
    ) -> tuple:
        """List contracts with filtering."""
        query = db.query(Contract)

        if not include_deleted:
            query = query.filter(Contract.is_deleted == False)
        if status:
            query = query.filter(Contract.status == status)
        if owner_id:
            query = query.filter(Contract.owner_id == owner_id)
        if organization_id:
            query = query.filter(Contract.organization_id == organization_id)
        if search:
            safe_search = sanitize_search_input(search)
            query = query.filter(
                or_(
                    Contract.title.ilike(f"%{safe_search}%"),
                    Contract.contract_number.ilike(f"%{safe_search}%"),
                    Contract.description.ilike(f"%{safe_search}%")
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
        """Soft delete contract."""
        contract = ContractService.get_contract(db, contract_id)

        # Soft delete
        contract.is_deleted = True
        contract.deleted_at = datetime.now(timezone.utc)
        contract.deleted_by = user_id

        audit = AuditLog(
            user_id=user_id,
            contract_id=contract_id,
            action="DELETE",
            resource_type="contract",
            resource_id=contract_id
        )
        db.add(audit)

        db.commit()

    @staticmethod
    def restore_contract(db: Session, contract_id: int, user_id: int) -> Contract:
        """Restore a soft-deleted contract."""
        contract = db.query(Contract).filter(
            Contract.id == contract_id,
            Contract.is_deleted == True
        ).first()

        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deleted contract not found"
            )

        contract.is_deleted = False
        contract.deleted_at = None
        contract.deleted_by = None

        audit = AuditLog(
            user_id=user_id,
            contract_id=contract_id,
            action="RESTORE",
            resource_type="contract",
            resource_id=contract_id
        )
        db.add(audit)

        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def bulk_update_status(
        db: Session,
        contract_ids: list,
        new_status: str,
        user_id: int
    ) -> int:
        """Bulk update contract statuses."""
        updated = 0
        for cid in contract_ids:
            try:
                contract = ContractService.get_contract(db, cid)
                old_status = contract.status
                contract.status = new_status

                audit = AuditLog(
                    user_id=user_id,
                    contract_id=cid,
                    action="BULK_STATUS_UPDATE",
                    resource_type="contract",
                    resource_id=cid,
                    changes={"status": {"old": old_status, "new": new_status}}
                )
                db.add(audit)
                updated += 1
            except HTTPException:
                continue

        db.commit()
        return updated

    @staticmethod
    def bulk_delete(db: Session, contract_ids: list, user_id: int) -> int:
        """Bulk soft-delete contracts."""
        deleted = 0
        for cid in contract_ids:
            try:
                ContractService.delete_contract(db, cid, user_id)
                deleted += 1
            except HTTPException:
                continue
        return deleted

    @staticmethod
    def get_expiring_contracts(
        db: Session,
        days_ahead: int = 30,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """Get contracts expiring within N days."""
        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        query = db.query(Contract).filter(
            Contract.is_deleted == False,
            Contract.end_date != None,
            Contract.end_date >= today,
            Contract.end_date <= future_date,
            Contract.status.in_(["approved", "executed"])
        )

        total = query.count()
        contracts = query.order_by(Contract.end_date).offset(skip).limit(limit).all()
        return contracts, total

    @staticmethod
    def get_dashboard_stats(db: Session, owner_id: int = None, organization_id: int = None) -> dict:
        """Get dashboard statistics."""
        query = db.query(Contract).filter(Contract.is_deleted == False)

        if owner_id:
            query = query.filter(Contract.owner_id == owner_id)
        if organization_id:
            query = query.filter(Contract.organization_id == organization_id)

        all_contracts = query.all()
        today = date.today()

        stats = {
            "total_contracts": len(all_contracts),
            "draft_contracts": sum(1 for c in all_contracts if c.status == "draft"),
            "submitted_contracts": sum(1 for c in all_contracts if c.status == "submitted"),
            "approved_contracts": sum(1 for c in all_contracts if c.status == "approved"),
            "rejected_contracts": sum(1 for c in all_contracts if c.status == "rejected"),
            "executed_contracts": sum(1 for c in all_contracts if c.status == "executed"),
            "total_value": sum(c.value or 0 for c in all_contracts),
            "contracts_expiring_30d": sum(
                1 for c in all_contracts
                if c.end_date and today <= c.end_date <= today + timedelta(days=30)
            ),
            "contracts_expiring_60d": sum(
                1 for c in all_contracts
                if c.end_date and today <= c.end_date <= today + timedelta(days=60)
            ),
            "contracts_expiring_90d": sum(
                1 for c in all_contracts
                if c.end_date and today <= c.end_date <= today + timedelta(days=90)
            ),
        }
        return stats
