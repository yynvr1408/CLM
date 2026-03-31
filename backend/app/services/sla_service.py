"""SLA and renewal monitoring service."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.services.notification_service import NotificationService
from app.models.models import Renewal, Contract, User, AuditLog
from app.schemas.schemas import RenewalCreate, RenewalUpdate
from app.services.audit_service import AuditService
from fastapi import HTTPException, status
from datetime import date, datetime, timedelta
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class SLAService:
    """Service for SLA monitoring and renewal management."""
    
    @staticmethod
    def process_renewal_alerts(db: Session) -> int:
        """
        Check all pending renewals and send alerts if alert_date has passed.
        Returns the count of notifications sent.
        """
        today = date.today()
        
        # Find renewals where alert_date <= today and notification not yet sent
        to_alert = db.query(Renewal).filter(
            and_(
                Renewal.alert_date <= today,
                Renewal.notification_sent == False,
                Renewal.status == "pending"
            )
        ).all()

        sent_count = 0
        for renewal in to_alert:
            contract = db.query(Contract).filter(Contract.id == renewal.contract_id).first()
            if contract:
                owner = db.query(User).filter(User.id == contract.owner_id).first()
                if owner:
                    success = NotificationService.send_renewal_alert(
                        to_email=owner.email,
                        contract_title=contract.title,
                        contract_number=contract.contract_number,
                        renewal_date=renewal.renewal_date.isoformat()
                    )
                    
                    if success:
                        renewal.notification_sent = True
                        renewal.status = "notified"
                        sent_count += 1
                        
                        # Add audit log
                        AuditService.log_action(
                            db, user_id=1, action="RENEWAL_ALERT_SENT",
                            resource_type="renewal", resource_id=renewal.id,
                            contract_id=contract.id
                        )

        db.commit()
        return sent_count
    
    @staticmethod
    def create_renewal(
        db: Session,
        contract_id: int,
        renewal_data: RenewalCreate
    ) -> Renewal:
        """Create renewal record for a contract."""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        new_renewal = Renewal(
            contract_id=contract_id,
            renewal_date=renewal_data.renewal_date,
            alert_date=renewal_data.alert_date,
            status="pending"
        )
        
        db.add(new_renewal)
        db.commit()
        db.refresh(new_renewal)
        
        return new_renewal
    
    @staticmethod
    def get_renewal(db: Session, renewal_id: int) -> Renewal:
        """Get renewal by ID."""
        renewal = db.query(Renewal).filter(Renewal.id == renewal_id).first()
        
        if not renewal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Renewal not found"
            )
        
        return renewal
    
    @staticmethod
    def get_contract_renewals(
        db: Session,
        contract_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Renewal], int]:
        """Get all renewals for a contract."""
        query = db.query(Renewal).filter(Renewal.contract_id == contract_id)
        
        total = query.count()
        renewals = query.order_by(desc(Renewal.renewal_date)).offset(skip).limit(limit).all()
        
        return renewals, total
    
    @staticmethod
    def get_upcoming_renewals(
        db: Session,
        days_ahead: int = 30,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Renewal], int]:
        """Get renewals that are being coming up."""
        today = date.today()
        future_date = today + timedelta(days=days_ahead)
        
        query = db.query(Renewal).filter(
            and_(
                Renewal.renewal_date >= today,
                Renewal.renewal_date <= future_date,
                Renewal.status == "pending"
            )
        )
        
        total = query.count()
        renewals = query.order_by(Renewal.renewal_date).offset(skip).limit(limit).all()
        
        return renewals, total
    
    @staticmethod
    def get_overdue_renewals(
        db: Session,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Renewal], int]:
        """Get overdue renewals."""
        today = date.today()
        
        query = db.query(Renewal).filter(
            and_(
                Renewal.renewal_date < today,
                Renewal.status.in_(["pending", "notified"])
            )
        )
        
        total = query.count()
        renewals = query.order_by(Renewal.renewal_date).offset(skip).limit(limit).all()
        
        return renewals, total
    
    @staticmethod
    def mark_renewal_notified(db: Session, renewal_id: int) -> Renewal:
        """Mark renewal as notified."""
        renewal = SLAService.get_renewal(db, renewal_id)
        
        renewal.notification_sent = True
        renewal.status = "notified"
        renewal.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(renewal)
        
        return renewal
    
    @staticmethod
    def mark_renewal_renewed(db: Session, renewal_id: int, user_id: int) -> Renewal:
        """Mark renewal as renewed."""
        renewal = SLAService.get_renewal(db, renewal_id)
        
        contract = db.query(Contract).filter(Contract.id == renewal.contract_id).first()
        
        renewal.status = "renewed"
        renewal.updated_at = datetime.utcnow()
        
        # Unified Secure Audit log
        AuditService.log_action(
            db, 
            user_id=user_id,
            action="RENEW",
            resource_type="renewal",
            resource_id=renewal_id,
            contract_id=contract.id
        )
        db.refresh(renewal)
        
        return renewal
    
    @staticmethod
    def update_renewal(
        db: Session,
        renewal_id: int,
        renewal_data: RenewalUpdate
    ) -> Renewal:
        """Update renewal status."""
        renewal = SLAService.get_renewal(db, renewal_id)
        
        renewal.status = renewal_data.status
        renewal.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(renewal)
        
        return renewal
