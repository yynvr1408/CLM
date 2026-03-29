"""In-app notification service."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import Notification
from fastapi import HTTPException, status


class InAppNotificationService:
    """Service for in-app notifications."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        type: str,
        title: str,
        message: str,
        link: str = None,
    ) -> Notification:
        """Create an in-app notification."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple:
        """Get notifications for a user."""
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        total = query.count()
        notifications = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
        return notifications, total

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """Get count of unread notifications."""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).count()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Notification:
        """Mark a notification as read."""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        ).first()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """Mark all notifications as read."""
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).update({"is_read": True})
        db.commit()
        return count

    @staticmethod
    def delete_notification(db: Session, notification_id: int, user_id: int) -> None:
        """Delete a notification."""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        ).first()

        if notification:
            db.delete(notification)
            db.commit()

    @staticmethod
    def notify_approval_request(
        db: Session,
        approver_id: int,
        contract_title: str,
        contract_number: str,
        contract_id: int,
    ):
        """Create notification for approval request."""
        InAppNotificationService.create_notification(
            db,
            user_id=approver_id,
            type="approval_request",
            title="Approval Required",
            message=f"Contract {contract_number} ({contract_title}) requires your approval",
            link=f"/contracts/{contract_id}",
        )

    @staticmethod
    def notify_status_change(
        db: Session,
        user_id: int,
        contract_title: str,
        old_status: str,
        new_status: str,
        contract_id: int,
    ):
        """Create notification for contract status change."""
        InAppNotificationService.create_notification(
            db,
            user_id=user_id,
            type="status_change",
            title="Contract Status Updated",
            message=f"Contract '{contract_title}' changed from {old_status} to {new_status}",
            link=f"/contracts/{contract_id}",
        )

    @staticmethod
    def notify_renewal(
        db: Session,
        user_id: int,
        contract_title: str,
        renewal_date: str,
        contract_id: int,
    ):
        """Create notification for upcoming renewal."""
        InAppNotificationService.create_notification(
            db,
            user_id=user_id,
            type="renewal",
            title="Contract Renewal Alert",
            message=f"Contract '{contract_title}' is due for renewal on {renewal_date}",
            link=f"/contracts/{contract_id}",
        )
