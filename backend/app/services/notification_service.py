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
