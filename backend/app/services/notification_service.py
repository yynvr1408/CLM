"""Notification service."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from typing import List, Dict, Optional
import json
import httpx


class NotificationService:
    """Service for email and webhook notifications."""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email notification."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.EMAILS_FROM_EMAIL
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Attach text version
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML version if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send email via SMTP
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    @staticmethod
    def send_approval_notification(
        to_email: str,
        approver_name: str,
        contract_title: str,
        contract_number: str
    ) -> bool:
        """Send approval notification email."""
        subject = f"Contract Approval Required: {contract_number}"
        
        body = f"""
Hi {approver_name},

A contract requires your approval:

Contract: {contract_title}
Contract Number: {contract_number}

Please log in to the CLM platform to review and approve/reject this contract.

Best regards,
CLM Platform
        """.strip()
        
        return NotificationService.send_email(to_email, subject, body)
    
    @staticmethod
    def send_renewal_alert(
        to_email: str,
        contract_title: str,
        contract_number: str,
        renewal_date: str
    ) -> bool:
        """Send contract renewal alert email."""
        subject = f"Contract Renewal Alert: {contract_number}"
        
        body = f"""
Hello,

This is a reminder that the following contract is coming up for renewal:

Contract: {contract_title}
Contract Number: {contract_number}
Renewal Date: {renewal_date}

Please log in to the CLM platform to manage the renewal process.

Best regards,
CLM Platform
        """.strip()
        
        return NotificationService.send_email(to_email, subject, body)
    
    @staticmethod
    def send_status_change_notification(
        to_email: str,
        contract_title: str,
        old_status: str,
        new_status: str
    ) -> bool:
        """Send contract status change notification."""
        subject = f"Contract Status Updated: {contract_title}"
        
        body = f"""
Hello,

The status of contract "{contract_title}" has been updated:

Previous Status: {old_status}
New Status: {new_status}

Log in to the CLM platform for more details.

Best regards,
CLM Platform
        """.strip()
        
        return NotificationService.send_email(to_email, subject, body)
    
    @staticmethod
    async def send_webhook(
        url: str,
        event_type: str,
        data: Dict,
        headers: Optional[Dict] = None
    ) -> bool:
        """Send webhook notification."""
        try:
            payload = {
                "event": event_type,
                "data": data
            }
            
            webhook_headers = headers or {}
            webhook_headers['Content-Type'] = 'application/json'
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=webhook_headers,
                    timeout=10.0
                )
                
                return response.status_code in [200, 201, 202, 204]
        except Exception as e:
            print(f"Error sending webhook: {str(e)}")
            return False
    
    @staticmethod
    def send_contract_created_notification(
        to_email: str,
        contract_title: str,
        contract_number: str
    ) -> bool:
        """Send contract created notification."""
        subject = f"Contract Created: {contract_number}"
        
        body = f"""
Hello,

A new contract has been created:

Contract: {contract_title}
Contract Number: {contract_number}

Log in to the CLM platform to view details.

Best regards,
CLM Platform
        """.strip()
        
        return NotificationService.send_email(to_email, subject, body)

    @staticmethod
    def send_registration_welcome_email(
        to_email: str,
        username: str,
        full_name: str,
        requires_approval: bool = True
    ) -> bool:
        """Send welcome email to newly registered user."""
        subject = "Welcome to CLM Platform"

        if requires_approval:
            status_msg = (
                "Your account has been created and is pending admin approval. "
                "You will receive another email once your account has been activated."
            )
        else:
            status_msg = (
                "Your account has been created and is ready to use. "
                "You can log in to the CLM platform right away."
            )

        body = f"""
Hi {full_name},

Welcome to the Contract Lifecycle Management (CLM) Platform!

Your account details:
  Username: {username}
  Email: {to_email}

{status_msg}

If you did not register for this account, please ignore this email.

Best regards,
CLM Platform Team
        """.strip()

        html_body = f"""
<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
  <div style="background: linear-gradient(135deg, #6366f1, #818cf8); padding: 32px; border-radius: 12px 12px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0; font-size: 24px;">Welcome to CLM Platform</h1>
  </div>
  <div style="background: #ffffff; padding: 32px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
    <p style="color: #334155; font-size: 16px;">Hi <strong>{full_name}</strong>,</p>
    <p style="color: #475569;">Welcome to the Contract Lifecycle Management Platform!</p>
    <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
      <tr><td style="padding: 8px; color: #64748b;">Username:</td><td style="padding: 8px; font-weight: 600;">{username}</td></tr>
      <tr><td style="padding: 8px; color: #64748b;">Email:</td><td style="padding: 8px; font-weight: 600;">{to_email}</td></tr>
    </table>
    <div style="background: #f8fafc; padding: 16px; border-radius: 8px; border-left: 4px solid #6366f1; margin: 16px 0;">
      <p style="color: #475569; margin: 0;">{status_msg}</p>
    </div>
    <p style="color: #94a3b8; font-size: 12px; margin-top: 24px;">If you did not register for this account, please ignore this email.</p>
  </div>
</div>
        """.strip()

        return NotificationService.send_email(to_email, subject, body, html_body=html_body)

    @staticmethod
    def send_new_user_admin_alert(
        to_email: str,
        admin_name: str,
        new_user_email: str,
        new_user_name: str
    ) -> bool:
        """Notify admin that a new user has registered and needs approval."""
        subject = f"New User Registration: {new_user_name}"

        body = f"""
Hi {admin_name},

A new user has registered on the CLM Platform and requires your approval:

Name: {new_user_name}
Email: {new_user_email}

Please log in to the admin panel to review and approve this registration.

Best regards,
CLM Platform
        """.strip()

        return NotificationService.send_email(to_email, subject, body)

    @staticmethod
    def send_daily_digest(
        to_email: str,
        user_name: str,
        actions: list,
        stats: dict = None
    ) -> bool:
        """
        Send a daily digest email combining all user actions from the past 24 hours.
        
        Args:
            to_email: Recipient email
            user_name: User's display name
            actions: List of dicts with keys: action, resource_type, resource_id, timestamp
            stats: Optional dict with summary stats (contracts_created, approvals_pending, etc.)
        """
        from datetime import date as date_type
        today = date_type.today().isoformat()
        subject = f"CLM Daily Digest — {today}"

        if not actions:
            return False  # Don't send empty digests

        # Build plain text
        action_lines = []
        for a in actions:
            ts = a.get("timestamp", "")
            action_lines.append(f"  • [{ts}] {a.get('action', 'N/A')} on {a.get('resource_type', 'resource')} #{a.get('resource_id', '')}")

        stats_block = ""
        if stats:
            stats_block = f"""
Platform Summary:
  Total Contracts: {stats.get('total_contracts', 0)}
  Pending Approvals: {stats.get('pending_approvals', 0)}
  Upcoming Renewals: {stats.get('upcoming_renewals', 0)}
"""

        body = f"""
Hi {user_name},

Here's your daily activity summary for {today}:

Your Actions ({len(actions)} total):
{chr(10).join(action_lines)}
{stats_block}
Log in to the CLM platform for full details.

Best regards,
CLM Platform
        """.strip()

        # Build HTML version
        action_rows = ""
        for a in actions:
            ts = a.get("timestamp", "")
            action_rows += f"""
            <tr>
              <td style="padding: 8px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-size: 13px;">{ts}</td>
              <td style="padding: 8px 12px; border-bottom: 1px solid #f1f5f9; font-weight: 500;">{a.get('action', '')}</td>
              <td style="padding: 8px 12px; border-bottom: 1px solid #f1f5f9;">{a.get('resource_type', '')} #{a.get('resource_id', '')}</td>
            </tr>"""

        stats_html = ""
        if stats:
            stats_html = f"""
            <div style="display: flex; gap: 12px; margin: 16px 0;">
              <div style="flex: 1; background: #f0f9ff; padding: 12px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: 700; color: #6366f1;">{stats.get('total_contracts', 0)}</div>
                <div style="font-size: 11px; color: #64748b;">Total Contracts</div>
              </div>
              <div style="flex: 1; background: #fffbeb; padding: 12px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: 700; color: #f59e0b;">{stats.get('pending_approvals', 0)}</div>
                <div style="font-size: 11px; color: #64748b;">Pending Approvals</div>
              </div>
              <div style="flex: 1; background: #fef2f2; padding: 12px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: 700; color: #ef4444;">{stats.get('upcoming_renewals', 0)}</div>
                <div style="font-size: 11px; color: #64748b;">Upcoming Renewals</div>
              </div>
            </div>"""

        html_body = f"""
<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 640px; margin: 0 auto; padding: 24px;">
  <div style="background: linear-gradient(135deg, #0f172a, #1e293b); padding: 24px 32px; border-radius: 12px 12px 0 0;">
    <h1 style="color: white; margin: 0; font-size: 20px;">📋 Daily Digest — {today}</h1>
    <p style="color: #94a3b8; margin: 4px 0 0;">Hi {user_name}, here's your activity summary.</p>
  </div>
  <div style="background: #ffffff; padding: 24px 32px; border: 1px solid #e2e8f0; border-top: none;">
    {stats_html}
    <h3 style="color: #334155; margin: 20px 0 8px;">Your Actions ({len(actions)})</h3>
    <table style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr style="background: #f8fafc;">
          <th style="padding: 8px 12px; text-align: left; color: #64748b; font-size: 12px;">Time</th>
          <th style="padding: 8px 12px; text-align: left; color: #64748b; font-size: 12px;">Action</th>
          <th style="padding: 8px 12px; text-align: left; color: #64748b; font-size: 12px;">Resource</th>
        </tr>
      </thead>
      <tbody>
        {action_rows}
      </tbody>
    </table>
  </div>
  <div style="background: #f8fafc; padding: 16px 32px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0; border-top: none; text-align: center;">
    <p style="color: #94a3b8; font-size: 12px; margin: 0;">CLM Platform — Contract Lifecycle Management</p>
  </div>
</div>
        """.strip()

        return NotificationService.send_email(to_email, subject, body, html_body=html_body)
