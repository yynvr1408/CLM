"""Comment service for threaded contract discussions."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import Comment, Contract, Notification
from app.schemas.schemas import CommentCreate, CommentUpdate
from fastapi import HTTPException, status


class CommentService:
    """Service for comment operations."""

    @staticmethod
    def create_comment(
        db: Session,
        contract_id: int,
        user_id: int,
        comment_data: CommentCreate,
        user_name: str = "",
    ) -> Comment:
        """Create a comment on a contract."""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )

        # Validate parent comment
        if comment_data.parent_id:
            parent = db.query(Comment).filter(
                Comment.id == comment_data.parent_id,
                Comment.contract_id == contract_id,
            ).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent comment not found"
                )

        comment = Comment(
            contract_id=contract_id,
            user_id=user_id,
            parent_id=comment_data.parent_id,
            content=comment_data.content,
        )
        db.add(comment)
        db.flush()

        # Notify contract owner about new comment
        if contract.owner_id != user_id:
            notification = Notification(
                user_id=contract.owner_id,
                type="comment",
                title="New Comment",
                message=f"{user_name} commented on contract {contract.contract_number}",
                link=f"/contracts/{contract_id}",
            )
            db.add(notification)

        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def get_contract_comments(
        db: Session,
        contract_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """Get all top-level comments for a contract."""
        query = db.query(Comment).filter(
            Comment.contract_id == contract_id,
            Comment.parent_id == None,
        )

        total = query.count()
        comments = query.order_by(desc(Comment.created_at)).offset(skip).limit(limit).all()
        return comments, total

    @staticmethod
    def update_comment(
        db: Session,
        comment_id: int,
        user_id: int,
        comment_data: CommentUpdate,
    ) -> Comment:
        """Update a comment."""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own comments"
            )

        for field, value in comment_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(comment, field, value)

        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def delete_comment(db: Session, comment_id: int, user_id: int, is_admin: bool = False) -> None:
        """Delete a comment."""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        if comment.user_id != user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )

        db.delete(comment)
        db.commit()
