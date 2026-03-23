"""Workflow and approval service."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.models.models import Approval, Contract, AuditLog
from app.schemas.schemas import ApprovalCreate, ApprovalUpdate
from fastapi import HTTPException, status
from datetime import datetime


class WorkflowService:
    """Service for workflow and approval operations."""
    
    @staticmethod
    def create_approval(
        db: Session,
        contract_id: int,
        approval_data: ApprovalCreate
    ) -> Approval:
        """Create approval record."""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        new_approval = Approval(
            contract_id=contract_id,
            approver_id=approval_data.approver_id,
            approval_level=approval_data.approval_level,
            comments=approval_data.comments,
            status="pending"
        )
        
        db.add(new_approval)
        db.commit()
        db.refresh(new_approval)
        
        return new_approval
    
    @staticmethod
    def get_approval(db: Session, approval_id: int) -> Approval:
        """Get approval by ID."""
        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval not found"
            )
        
        return approval
    
    @staticmethod
    def get_contract_approvals(
        db: Session,
        contract_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """Get all approvals for a contract."""
        query = db.query(Approval).filter(Approval.contract_id == contract_id)
        
        total = query.count()
        approvals = query.order_by(Approval.approval_level).offset(skip).limit(limit).all()
        
        return approvals, total
    
    @staticmethod
    def approve_contract(
        db: Session,
        approval_id: int,
        user_id: int,
        comments: str = None
    ) -> Approval:
        """Approve a contract at given level."""
        approval = WorkflowService.get_approval(db, approval_id)
        
        if approval.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval already {approval.status}"
            )
        
        approval.status = "approved"
        approval.approved_at = datetime.utcnow()
        approval.comments = comments or approval.comments
        
        # Check if all approvals are complete
        contract = db.query(Contract).filter(Contract.id == approval.contract_id).first()
        all_approvals = db.query(Approval).filter(
            Approval.contract_id == contract.id
        ).all()
        
        all_approved = all(a.status == "approved" for a in all_approvals)
        
        if all_approved:
            contract.status = "approved"
        
        # Audit log
        audit = AuditLog(
            user_id=user_id,
            contract_id=contract.id,
            action="APPROVE",
            resource_type="approval",
            resource_id=approval_id
        )
        db.add(audit)
        
        db.commit()
        db.refresh(approval)
        
        return approval
    
    @staticmethod
    def reject_contract(
        db: Session,
        approval_id: int,
        user_id: int,
        comments: str
    ) -> Approval:
        """Reject a contract at given level."""
        approval = WorkflowService.get_approval(db, approval_id)
        
        if approval.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval already {approval.status}"
            )
        
        approval.status = "rejected"
        approval.comments = comments
        
        # Update contract status
        contract = db.query(Contract).filter(Contract.id == approval.contract_id).first()
        contract.status = "rejected"
        
        # Audit log
        audit = AuditLog(
            user_id=user_id,
            contract_id=contract.id,
            action="REJECT",
            resource_type="approval",
            resource_id=approval_id
        )
        db.add(audit)
        
        db.commit()
        db.refresh(approval)
        
        return approval
    
    @staticmethod
    def get_pending_approvals_for_user(
        db: Session,
        approver_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """Get pending approvals for a user."""
        query = db.query(Approval).filter(
            and_(
                Approval.approver_id == approver_id,
                Approval.status == "pending"
            )
        )
        
        total = query.count()
        approvals = query.order_by(Approval.created_at).offset(skip).limit(limit).all()
        
        return approvals, total
