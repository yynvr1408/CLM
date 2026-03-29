"""Contract template service."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import ContractTemplate, TemplateClause, Clause
from app.schemas.schemas import ContractTemplateCreate, ContractTemplateUpdate
from fastapi import HTTPException, status


class TemplateService:
    """Service for contract template operations."""

    @staticmethod
    def create_template(
        db: Session,
        template_data: ContractTemplateCreate,
        created_by_id: int,
        organization_id: int = None,
    ) -> ContractTemplate:
        """Create a new contract template."""
        template = ContractTemplate(
            name=template_data.name,
            description=template_data.description,
            contract_type=template_data.contract_type,
            default_fields=template_data.default_fields,
            approval_workflow=template_data.approval_workflow,
            organization_id=organization_id,
            created_by_id=created_by_id,
        )
        db.add(template)
        db.flush()

        # Add clauses
        for clause_link in template_data.clause_ids:
            clause = db.query(Clause).filter(Clause.id == clause_link.clause_id).first()
            if clause:
                tc = TemplateClause(
                    template_id=template.id,
                    clause_id=clause.id,
                    order=clause_link.order,
                    is_required=clause_link.is_required,
                )
                db.add(tc)

        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def get_template(db: Session, template_id: int) -> ContractTemplate:
        """Get template by ID."""
        template = db.query(ContractTemplate).filter(
            ContractTemplate.id == template_id,
            ContractTemplate.is_active == True,
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        return template

    @staticmethod
    def list_templates(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        organization_id: int = None,
        contract_type: str = None,
    ) -> tuple:
        """List templates."""
        query = db.query(ContractTemplate).filter(ContractTemplate.is_active == True)

        if organization_id:
            query = query.filter(ContractTemplate.organization_id == organization_id)
        if contract_type:
            query = query.filter(ContractTemplate.contract_type == contract_type)

        total = query.count()
        templates = query.order_by(desc(ContractTemplate.created_at)).offset(skip).limit(limit).all()
        return templates, total

    @staticmethod
    def update_template(
        db: Session,
        template_id: int,
        template_data: ContractTemplateUpdate,
    ) -> ContractTemplate:
        """Update template."""
        template = TemplateService.get_template(db, template_id)

        for field, value in template_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(template, field, value)

        template.version += 1
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: int) -> None:
        """Soft delete template (deactivate)."""
        template = TemplateService.get_template(db, template_id)
        template.is_active = False
        db.commit()
