"""Comment API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import CommentCreate, CommentUpdate, CommentResponse
from app.services.comment_service import CommentService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user, require_permission

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/contract/{contract_id}", response_model=CommentResponse, status_code=201)
def create_comment(
    contract_id: int,
    data: CommentCreate,
    current_user: User = require_permission("comments:create"),
    db: Session = Depends(get_db),
):
    """Create a comment on a contract."""
    comment = CommentService.create_comment(
        db, contract_id, current_user.id, data,
        user_name=current_user.full_name or current_user.username,
    )
    resp = CommentResponse.model_validate(comment)
    resp.user_name = current_user.full_name or current_user.username
    return resp


@router.get("/contract/{contract_id}", response_model=dict)
def get_contract_comments(
    contract_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = require_permission("comments:read"),
    db: Session = Depends(get_db),
):
    """Get comments for a contract."""
    comments, total = CommentService.get_contract_comments(db, contract_id, skip, limit)

    items = []
    for c in comments:
        resp = CommentResponse.model_validate(c)
        if c.user:
            resp.user_name = c.user.full_name or c.user.username
        items.append(resp)

    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: User = require_permission("comments:create"),
    db: Session = Depends(get_db),
):
    """Update a comment (own comments only)."""
    comment = CommentService.update_comment(db, comment_id, current_user.id, data)
    resp = CommentResponse.model_validate(comment)
    if comment.user:
        resp.user_name = comment.user.full_name or comment.user.username
    return resp


@router.delete("/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    current_user: User = require_permission("comments:delete"),
    db: Session = Depends(get_db),
):
    """Delete a comment."""
    CommentService.delete_comment(
        db, comment_id, current_user.id,
        is_admin=current_user.is_superuser,
    )
