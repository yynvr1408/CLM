"""Clause library API endpoints with RBAC."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import ClauseCreate, ClauseResponse, ClauseUpdate
from app.services.clause_service import ClauseService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user, require_permission

router = APIRouter(prefix="/clauses", tags=["clauses"])


@router.post("", response_model=ClauseResponse, status_code=status.HTTP_201_CREATED)
def create_clause(
    clause_data: ClauseCreate,
    current_user: User = require_permission("clauses:create"),
    db: Session = Depends(get_db)
):
    """Create a new reusable clause."""
    clause = ClauseService.create_clause(db, clause_data, current_user.id)
    return clause


@router.get("", response_model=dict)
def list_clauses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: str = Query(None),
    search: str = Query(None),
    current_user: User = require_permission("clauses:read"),
    db: Session = Depends(get_db)
):
    """List clauses with search and filtering."""
    if search:
        clauses, total = ClauseService.search_clauses(
            db, query_text=search, category=category, skip=skip, limit=limit
        )
    elif category:
        clauses, total = ClauseService.get_clauses_by_category(
            db, category=category, skip=skip, limit=limit
        )
    else:
        clauses, total = ClauseService.search_clauses(db, skip=skip, limit=limit)

    return {
        "total": total, "skip": skip, "limit": limit,
        "items": [ClauseResponse.model_validate(c) for c in clauses]
    }


@router.get("/{clause_id}", response_model=ClauseResponse)
def get_clause(
    clause_id: int,
    current_user: User = require_permission("clauses:read"),
    db: Session = Depends(get_db)
):
    """Get clause details."""
    return ClauseService.get_clause(db, clause_id)


@router.patch("/{clause_id}", response_model=ClauseResponse)
def update_clause(
    clause_id: int,
    clause_data: ClauseUpdate,
    current_user: User = require_permission("clauses:update"),
    db: Session = Depends(get_db)
):
    """Update clause."""
    return ClauseService.update_clause(db, clause_id, clause_data, current_user.id)


@router.delete("/{clause_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clause(
    clause_id: int,
    current_user: User = require_permission("clauses:delete"),
    db: Session = Depends(get_db)
):
    """Delete a clause (Super Admin only)."""
    # Strict role check as per user request
    from app.models.models import Role
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    
    if not current_user.is_superuser and (not role or role.name != "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only super_admin can delete clauses."
        )

    ClauseService.delete_clause(db, clause_id, current_user.id)
    return None


@router.get("/category/{category}", response_model=dict)
def get_clauses_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = require_permission("clauses:read"),
    db: Session = Depends(get_db)
):
    """Get clauses by category."""
    clauses, total = ClauseService.get_clauses_by_category(
        db, category=category, skip=skip, limit=limit
    )
    return {
        "total": total, "skip": skip, "limit": limit, "category": category,
        "items": [ClauseResponse.model_validate(c) for c in clauses]
    }
