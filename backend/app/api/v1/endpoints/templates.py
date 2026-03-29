"""Contract template API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import (
    ContractTemplateCreate, ContractTemplateUpdate, ContractTemplateResponse, ClauseResponse
)
from app.services.template_service import TemplateService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user, require_permission

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=ContractTemplateResponse, status_code=201)
def create_template(
    data: ContractTemplateCreate,
    current_user: User = require_permission("templates:create"),
    db: Session = Depends(get_db),
):
    """Create a new contract template."""
    template = TemplateService.create_template(
        db, data, current_user.id, current_user.organization_id,
    )
    resp = ContractTemplateResponse.model_validate(template)
    resp.clauses = [ClauseResponse.model_validate(tc.clause) for tc in template.template_clauses if tc.clause]
    return resp


@router.get("", response_model=dict)
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    contract_type: str = Query(None),
    current_user: User = require_permission("templates:read"),
    db: Session = Depends(get_db),
):
    """List templates."""
    templates, total = TemplateService.list_templates(
        db, skip=skip, limit=limit,
        organization_id=current_user.organization_id,
        contract_type=contract_type,
    )
    items = []
    for t in templates:
        resp = ContractTemplateResponse.model_validate(t)
        resp.clauses = [ClauseResponse.model_validate(tc.clause) for tc in t.template_clauses if tc.clause]
        items.append(resp)

    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/{template_id}", response_model=ContractTemplateResponse)
def get_template(
    template_id: int,
    current_user: User = require_permission("templates:read"),
    db: Session = Depends(get_db),
):
    """Get template details."""
    template = TemplateService.get_template(db, template_id)
    resp = ContractTemplateResponse.model_validate(template)
    resp.clauses = [ClauseResponse.model_validate(tc.clause) for tc in template.template_clauses if tc.clause]
    return resp


@router.patch("/{template_id}", response_model=ContractTemplateResponse)
def update_template(
    template_id: int,
    data: ContractTemplateUpdate,
    current_user: User = require_permission("templates:update"),
    db: Session = Depends(get_db),
):
    """Update template."""
    template = TemplateService.update_template(db, template_id, data)
    resp = ContractTemplateResponse.model_validate(template)
    resp.clauses = [ClauseResponse.model_validate(tc.clause) for tc in template.template_clauses if tc.clause]
    return resp


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    current_user: User = require_permission("templates:delete"),
    db: Session = Depends(get_db),
):
    """Delete template (deactivate)."""
    TemplateService.delete_template(db, template_id)
