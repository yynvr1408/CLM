"""Notification API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import NotificationResponse, NotificationMarkRead
from app.services.inapp_notification_service import InAppNotificationService
from app.models.models import User
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=dict)
def get_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's notifications."""
    notifications, total = InAppNotificationService.get_user_notifications(
        db, current_user.id, unread_only=unread_only, skip=skip, limit=limit
    )
    return {
        "total": total, "skip": skip, "limit": limit,
        "unread_count": InAppNotificationService.get_unread_count(db, current_user.id),
        "items": [NotificationResponse.model_validate(n) for n in notifications]
    }


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get unread notification count."""
    count = InAppNotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.post("/mark-read")
def mark_notifications_read(
    data: NotificationMarkRead,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark notifications as read."""
    if data.mark_all:
        count = InAppNotificationService.mark_all_as_read(db, current_user.id)
        return {"marked_read": count}

    for nid in data.notification_ids:
        InAppNotificationService.mark_as_read(db, nid, current_user.id)
    return {"marked_read": len(data.notification_ids)}


@router.delete("/{notification_id}", status_code=204)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a notification."""
    InAppNotificationService.delete_notification(db, notification_id, current_user.id)
