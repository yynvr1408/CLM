"""Audit and integrity service for tamper-proof logging."""
import json
import hashlib
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, between
from app.models.models import AuditLog, utcnow
from datetime import date, datetime, timedelta
from typing import List, Tuple, Dict

class AuditService:
    """Service for managing secure audit logs."""

    @staticmethod
    def _calculate_hash(data: dict) -> str:
        """Calculate SHA-256 hash of a dictionary."""
        # Ensure consistent ordering for hashing
        encoded = json.dumps(data, sort_keys=True, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def log_action(
        db: Session,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        clause_id: Optional[int] = None,
        changes: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create a new tamper-proof audit log entry."""
        # Get the previous record to link the chain
        last_log = db.query(AuditLog).order_by(desc(AuditLog.id)).first()
        previous_hash = last_log.entry_hash if last_log else None

        # Prepare base data for this entry
        log_data = {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "contract_id": contract_id,
            "clause_id": clause_id,
            "changes": changes,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "previous_hash": previous_hash
        }

        # Calculate this entry's hash
        entry_hash = AuditService._calculate_hash(log_data)

        # Create record
        new_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            contract_id=contract_id,
            clause_id=clause_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            previous_hash=previous_hash,
            entry_hash=entry_hash
        )

        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        
        return new_log

    @staticmethod
    def verify_chain(db: Session) -> dict:
        """Verify the integrity of the audit log chain."""
        logs = db.query(AuditLog).order_by(AuditLog.id).all()
        
        is_valid = True
        broken_id = None
        
        previous_hash = None
        for log in logs:
            # 1. Check if previous_hash matches
            if log.previous_hash != previous_hash:
                is_valid = False
                broken_id = log.id
                break
            
            # 2. Recalculate hash (excluding the hash itself and ID)
            current_log_data = {
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "contract_id": log.contract_id,
                "clause_id": log.clause_id,
                "changes": log.changes,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "previous_hash": log.previous_hash
            }
            
            recalculated_hash = AuditService._calculate_hash(current_log_data)
            
            # 3. Verify entry hash
            if recalculated_hash != log.entry_hash:
                is_valid = False
                broken_id = log.id
                break
            
            previous_hash = log.entry_hash
            
        return {
            "is_valid": is_valid,
            "broken_id": broken_id,
            "total_logs": len(logs)
        }

    @staticmethod
    def get_audit_logs(
        db: Session,
        user_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """Get paginated audit logs with filtering."""
        query = db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if contract_id:
            query = query.filter(AuditLog.contract_id == contract_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
            
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
        """Get recent activity for a specific user."""
        start_date = datetime.now() - timedelta(days=days)
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
    def export_audit_trail(db: Session, contract_id: int) -> List[Dict[str, Any]]:
        """Export simplified audit trail for external reporting."""
        logs = db.query(AuditLog).filter(AuditLog.contract_id == contract_id).order_by(AuditLog.created_at).all()
        
        export_data = []
        for log in logs:
            export_data.append({
                "timestamp": log.created_at.isoformat(),
                "user": log.user.full_name if log.user else f"User {log.user_id}",
                "action": log.action,
                "resource": log.resource_type,
                "changes": log.changes,
                "hash": log.entry_hash
            })
        return export_data
