"""Audit logging service."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.models.models import AuditLog
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta


class AuditService:
    """Service for audit logging and compliance."""
    
    @staticmethod
    def log_action(
        db: Session,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry."""
        audit = AuditLog(
            user_id=user_id,
            contract_id=contract_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit)
        db.commit()
        db.refresh(audit)
        
        return audit
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        user_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """Get audit logs with filtering."""
        query = db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if contract_id:
            query = query.filter(AuditLog.contract_id == contract_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        total = query.count()
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        
        return logs, total
    
    @staticmethod
    def get_contract_audit_trail(
        db: Session,
        contract_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """Get complete audit trail for a contract."""
        query = db.query(AuditLog).filter(AuditLog.contract_id == contract_id)
        
        total = query.count()
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        
        return logs, total
    
    @staticmethod
    def get_user_activity(
        db: Session,
        user_id: int,
        days: int = 30,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """Get user activity for last N days."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.created_at >= start_date
            )
        )
        
        total = query.count()
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        
        return logs, total
    
    @staticmethod
    def export_audit_trail(
        db: Session,
        contract_id: int
    ) -> List[Dict]:
        """Export contract audit trail as list of dicts."""
        logs, _ = AuditService.get_contract_audit_trail(db, contract_id, limit=10000)
        
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "changes": log.changes,
                "created_at": log.created_at.isoformat(),
                "ip_address": log.ip_address
            }
            for log in logs
        ]
