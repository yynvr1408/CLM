"""Clause library API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.schemas import (
    ClauseCreate, ClauseResponse, ClauseUpdate
)
from app.services.clause_service import ClauseService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/clauses", tags=["clauses"])


@router.post("", response_model=ClauseResponse, status_code=status.HTTP_201_CREATED)
def create_clause(
    clause_data: ClauseCreate,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List clauses with search and filtering."""
    if search:
        clauses, total = ClauseService.search_clauses(
            db,
            query_text=search,
            category=category,
            skip=skip,
            limit=limit
        )
    elif category:
        clauses, total = ClauseService.get_clauses_by_category(
            db,
            category=category,
            skip=skip,
            limit=limit
        )
    else:
        clauses, total = ClauseService.search_clauses(
            db,
            skip=skip,
            limit=limit
        )
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [ClauseResponse.model_validate(c) for c in clauses]
    }


@router.get("/{clause_id}", response_model=ClauseResponse)
def get_clause(
    clause_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get clause details."""
    clause = ClauseService.get_clause(db, clause_id)
    return clause


@router.patch("/{clause_id}", response_model=ClauseResponse)
def update_clause(
    clause_id: int,
    clause_data: ClauseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update clause."""
    clause = ClauseService.update_clause(db, clause_id, clause_data, current_user.id)
    return clause


@router.post("/{clause_id}/deactivate")
def deactivate_clause(
    clause_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate a clause."""
    clause = ClauseService.deactivate_clause(db, clause_id, current_user.id)
    return ClauseResponse.model_validate(clause)


@router.get("/category/{category}", response_model=dict)
def get_clauses_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get clauses by category."""
    clauses, total = ClauseService.get_clauses_by_category(
        db,
        category=category,
        skip=skip,
        limit=limit
    )
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "category": category,
        "items": [ClauseResponse.model_validate(c) for c in clauses]
    }
