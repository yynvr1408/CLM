"""Daily digest background task.

This module provides the daily digest job that collects all user actions
from the past 24 hours and sends a single consolidated email to each user.

Can be triggered via:
  1. A scheduled cron job calling the /api/v1/admin/send-daily-digest endpoint
  2. A background task scheduler (APScheduler, Celery, etc.)
  3. Manual invocation via CLI
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.models import AuditLog, User, Organization
from app.services.notification_service import NotificationService
from app.services.contract_service import ContractService
import logging

logger = logging.getLogger(__name__)

# Fixed default renewal alert window (in days)
DEFAULT_RENEWAL_ALERT_DAYS = 30


def get_org_renewal_alert_days(org: Organization) -> int:
    """
    Get the renewal alert window for an organization.
    
    Supports BOTH configurable per-org AND a fixed default:
    - If the org has a 'renewal_alert_days' setting, use it.
    - Otherwise, fall back to the fixed 30-day default.
    """
    if org and org.settings and isinstance(org.settings, dict):
        custom_days = org.settings.get("renewal_alert_days")
        if custom_days and isinstance(custom_days, int) and custom_days > 0:
            return custom_days
    return DEFAULT_RENEWAL_ALERT_DAYS


def send_daily_digests(db: Session) -> int:
    """
    Collect all audit log entries from the past 24 hours, group by user,
    and send a single consolidated daily digest email to each user.
    
    Returns the number of digest emails sent.
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    # Get all audit logs from the past 24 hours
    recent_logs = db.query(AuditLog).filter(
        AuditLog.created_at >= since
    ).order_by(AuditLog.created_at).all()

    if not recent_logs:
        logger.info("No actions in the past 24 hours, skipping daily digest.")
        return 0

    # Group by user_id
    user_actions: dict = {}
    for log in recent_logs:
        uid = log.user_id
        if uid not in user_actions:
            user_actions[uid] = []
        user_actions[uid].append({
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "timestamp": log.created_at.strftime("%H:%M") if log.created_at else "",
        })

    sent_count = 0
    for user_id, actions in user_actions.items():
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active or not user.email:
            continue

        # Get personalized stats for this user
        try:
            stats = ContractService.get_dashboard_stats(
                db, owner_id=user_id,
                organization_id=user.organization_id
            )
        except Exception:
            stats = None

        try:
            success = NotificationService.send_daily_digest(
                to_email=user.email,
                user_name=user.full_name or user.username,
                actions=actions,
                stats=stats
            )
            if success:
                sent_count += 1
                logger.info(f"Daily digest sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send daily digest to {user.email}: {e}")

    logger.info(f"Daily digest complete: {sent_count} emails sent.")
    return sent_count
