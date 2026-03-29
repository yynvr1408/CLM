"""Tag API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import TagCreate, TagResponse
from app.services.tag_service import TagService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user, require_permission

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagResponse, status_code=201)
def create_tag(
    data: TagCreate,
    current_user: User = require_permission("tags:create"),
    db: Session = Depends(get_db),
):
    """Create a new tag."""
    return TagService.create_tag(db, data, current_user.organization_id)


@router.get("", response_model=dict)
def list_tags(
    current_user: User = require_permission("tags:read"),
    db: Session = Depends(get_db),
):
    """List all tags."""
    tags = TagService.list_tags(db, current_user.organization_id)
    return {"items": [TagResponse.model_validate(t) for t in tags], "total": len(tags)}


@router.delete("/{tag_id}", status_code=204)
def delete_tag(
    tag_id: int,
    current_user: User = require_permission("tags:delete"),
    db: Session = Depends(get_db),
):
    """Delete a tag."""
    TagService.delete_tag(db, tag_id)


@router.post("/contract/{contract_id}/tag/{tag_id}")
def add_tag_to_contract(
    contract_id: int,
    tag_id: int,
    current_user: User = require_permission("contracts:update"),
    db: Session = Depends(get_db),
):
    """Add tag to contract."""
    TagService.add_tag_to_contract(db, contract_id, tag_id)
    return {"message": "Tag added"}


@router.delete("/contract/{contract_id}/tag/{tag_id}", status_code=204)
def remove_tag_from_contract(
    contract_id: int,
    tag_id: int,
    current_user: User = require_permission("contracts:update"),
    db: Session = Depends(get_db),
):
    """Remove tag from contract."""
    TagService.remove_tag_from_contract(db, contract_id, tag_id)
