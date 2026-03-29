"""Tag service for contract categorization."""
from sqlalchemy.orm import Session
from app.models.models import Tag, ContractTag
from app.schemas.schemas import TagCreate
from fastapi import HTTPException, status


class TagService:
    """Service for tag operations."""

    @staticmethod
    def create_tag(db: Session, tag_data: TagCreate, organization_id: int = None) -> Tag:
        """Create a new tag."""
        existing = db.query(Tag).filter(
            Tag.name == tag_data.name,
            Tag.organization_id == organization_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag already exists"
            )

        tag = Tag(
            name=tag_data.name,
            color=tag_data.color,
            organization_id=organization_id,
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    @staticmethod
    def list_tags(db: Session, organization_id: int = None) -> list:
        """List all tags."""
        query = db.query(Tag)
        if organization_id:
            query = query.filter(Tag.organization_id == organization_id)
        return query.order_by(Tag.name).all()

    @staticmethod
    def delete_tag(db: Session, tag_id: int) -> None:
        """Delete a tag and remove associations."""
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )

        # Remove associations
        db.query(ContractTag).filter(ContractTag.tag_id == tag_id).delete()
        db.delete(tag)
        db.commit()

    @staticmethod
    def add_tag_to_contract(db: Session, contract_id: int, tag_id: int) -> ContractTag:
        """Add a tag to a contract."""
        existing = db.query(ContractTag).filter(
            ContractTag.contract_id == contract_id,
            ContractTag.tag_id == tag_id,
        ).first()
        if existing:
            return existing

        ct = ContractTag(contract_id=contract_id, tag_id=tag_id)
        db.add(ct)
        db.commit()
        db.refresh(ct)
        return ct

    @staticmethod
    def remove_tag_from_contract(db: Session, contract_id: int, tag_id: int) -> None:
        """Remove a tag from a contract."""
        ct = db.query(ContractTag).filter(
            ContractTag.contract_id == contract_id,
            ContractTag.tag_id == tag_id,
        ).first()
        if ct:
            db.delete(ct)
            db.commit()
