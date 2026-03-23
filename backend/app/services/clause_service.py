"""Clause library service."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.models.models import Clause, AuditLog
from app.schemas.schemas import ClauseCreate, ClauseUpdate
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
        
        return new_clause
    
    @staticmethod
    def get_clause(db: Session, clause_id: int) -> Clause:
        """Get clause by ID."""
        clause = db.query(Clause).filter(Clause.id == clause_id).first()
        
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
        
        # Store changes
        changes = {}
        
        # Update fields
        for field, value in clause_data.dict(exclude_unset=True).items():
            if value is not None:
                old_value = getattr(clause, field, None)
                setattr(clause, field, value)
                changes[field] = {"old": old_value, "new": value}
        
        # Increment version
        clause.version += 1
        
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
        
        db.commit()
        db.refresh(clause)
        
        return clause
