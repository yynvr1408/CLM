"""Clause library service."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.models.models import Clause, AuditLog, ClauseVersion
from app.schemas.schemas import ClauseCreate, ClauseUpdate
from app.services.audit_service import AuditService
from fastapi import HTTPException, status


class ClauseService:
    """Service for clause operations."""
    
    @staticmethod
    def create_clause(
        db: Session,
        clause_data: ClauseCreate,
        created_by_id: int
    ) -> Clause:
        """Create a new reusable clause."""
        new_clause = Clause(
            title=clause_data.title,
            content=clause_data.content,
            category=clause_data.category,
            version=1,
            is_active=True,
            created_by_id=created_by_id
        )
        
        db.add(new_clause)
        db.commit()
        db.refresh(new_clause)
        
        # Audit log
        AuditService.log_action(
            db, user_id=created_by_id, action="CREATE",
            resource_type="clause", resource_id=new_clause.id,
            clause_id=new_clause.id,
            changes={"title": new_clause.title, "category": new_clause.category}
        )
        
        return new_clause
    
    @staticmethod
    def delete_clause(db: Session, clause_id: int, user_id: int) -> bool:
        """Physical delete of a clause (Super Admin only check handled in API)."""
        clause = ClauseService.get_clause(db, clause_id)
        
        # Log DELETE action first
        AuditService.log_action(
            db, user_id=user_id, action="DELETE",
            resource_type="clause", resource_id=clause_id,
            clause_id=clause_id,
            changes={"title": clause.title, "action": "Permanent deletion"}
        )
        
        db.delete(clause)
        db.commit()
        return True

    @staticmethod
    def get_clause(db: Session, clause_id: int) -> Clause:
        """Get clause by ID with attachments."""
        from sqlalchemy.orm import joinedload
        clause = db.query(Clause).options(joinedload(Clause.attachments)).filter(Clause.id == clause_id).first()
        
        if not clause:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clause not found"
            )
        
        return clause
    
    @staticmethod
    def update_clause(
        db: Session,
        clause_id: int,
        clause_data: ClauseUpdate,
        user_id: int
    ) -> Clause:
        """Update clause and increment version."""
        clause = ClauseService.get_clause(db, clause_id)
        
        # 1. Create a version record BEFORE updating current
        old_version = ClauseVersion(
            clause_id=clause.id,
            version_number=clause.version,
            title=clause.title,
            content=clause.content,
            category=clause.category,
            created_by_id=user_id
        )
        db.add(old_version)
        
        # Store changes for Audit Log
        changes = {}
        
        # 2. Update fields
        for field, value in clause_data.dict(exclude_unset=True).items():
            if value is not None:
                old_value = getattr(clause, field, None)
                if old_value != value:
                    setattr(clause, field, value)
                    changes[field] = {"old": str(old_value), "new": str(value)}
        
        # 3. Increment version
        clause.version += 1
        
        # Audit log
        AuditService.log_action(
            db, user_id=user_id, action="UPDATE",
            resource_type="clause", resource_id=clause_id,
            clause_id=clause_id,
            changes=changes
        )
        
        db.commit()
        db.refresh(clause)
        
        return clause
    
    @staticmethod
    def search_clauses(
        db: Session,
        query_text: str = "",
        category: str = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """Search clauses using full text search."""
        query = db.query(Clause).filter(Clause.is_active == True)
        
        if query_text:
            # Simple search - can be enhanced with PostgreSQL tsvector
            query = query.filter(
                or_(
                    Clause.title.ilike(f"%{query_text}%"),
                    Clause.content.ilike(f"%{query_text}%")
                )
            )
        
        if category:
            query = query.filter(Clause.category == category)
        
        total = query.count()
        clauses = query.order_by(desc(Clause.created_at)).offset(skip).limit(limit).all()
        
        return clauses, total
    
    @staticmethod
    def get_clauses_by_category(
        db: Session,
        category: str,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """Get clauses by category."""
        query = db.query(Clause).filter(
            (Clause.category == category) & (Clause.is_active == True)
        )
        
        total = query.count()
        clauses = query.order_by(desc(Clause.created_at)).offset(skip).limit(limit).all()
        
        return clauses, total
    
    @staticmethod
    def deactivate_clause(db: Session, clause_id: int, user_id: int) -> Clause:
        """Deactivate a clause."""
        clause = ClauseService.get_clause(db, clause_id)
        
        clause.is_active = False
        
        # Audit log
        AuditService.log_action(
            db, user_id=user_id, action="DEACTIVATE",
            resource_type="clause", resource_id=clause_id,
            clause_id=clause_id
        )
        
        db.commit()
        db.refresh(clause)
        
        return clause

    @staticmethod
    def restore_version(db: Session, clause_id: int, version_id: int, user_id: int) -> Clause:
        """Restore a clause to a previous version."""
        clause = ClauseService.get_clause(db, clause_id)
        version_record = db.query(ClauseVersion).filter(
            ClauseVersion.id == version_id,
            ClauseVersion.clause_id == clause_id
        ).first()

        if not version_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clause version not found"
            )

        # Before restoring, save CURRENT state as a new version
        current_historical = ClauseVersion(
            clause_id=clause.id,
            version_number=clause.version,
            title=clause.title,
            content=clause.content,
            category=clause.category,
            created_by_id=user_id
        )
        db.add(current_historical)

        # Map back fields
        changes = {
            "title": {"old": clause.title, "new": version_record.title},
            "content": {"old": "Updated (content diff)", "new": "Restored"},
            "version": {"old": clause.version, "new": clause.version + 1}
        }
        
        clause.title = version_record.title
        clause.content = version_record.content
        clause.category = version_record.category
        clause.version += 1

        # Audit log
        AuditService.log_action(
            db, user_id=user_id, action="RESTORE",
            resource_type="clause", resource_id=clause_id,
            clause_id=clause_id,
            changes=changes
        )

        db.commit()
        db.refresh(clause)
        return clause
