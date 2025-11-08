import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class EmailChannel:
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = ', '.join(to)
            msg['Subject'] = subject
            
            # Add text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f"attachment; filename= {attachment['filename']}"
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_template(
        self,
        to: List[str],
        template_name: str,
        context: dict
    ) -> bool:
        """Send email using template"""
        templates = {
            "execution_completed": {
                "subject": "Script Execution Completed: {script_name}",
                "body": '''
                    Script: {script_name}
                    Status: {status}
                    Duration: {duration}
                    Executed by: {user}
                    
                    View details: {execution_url}
                '''
            },
            "approval_request": {
                "subject": "Approval Required: {action}",
                "body": '''
                    Requester: {requester}
                    Action: {action}
                    Resource: {resource}
                    Reason: {reason}
                    
                    Approve: {approve_url}
                    Reject: {reject_url}
                '''
            },
            "execution_failed": {
                "subject": "Script Execution Failed: {script_name}",
                "body": '''
                    Script: {script_name}
                    Error: {error}
                    Executed by: {user}
                    
                    View logs: {execution_url}
                '''
            }
        }
        
        template = templates.get(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return False
        
        subject = template["subject"].format(**context)
        body = template["body"].format(**context)
        
        return await self.send(to, subject, body)