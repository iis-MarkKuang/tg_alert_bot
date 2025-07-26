import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import os
from datetime import datetime


class EmailUtils:
    """
    Email utility class for sending emails via SMTP with AWS SES support.
    Based on Java implementation - uses plain username and password.
    """
    
    def __init__(self, 
                 smtp_server: str = "email-smtp.us-east-1.amazonaws.com",
                 smtp_port: int = 587,
                 username: str = "AKIA4Y34TXGODF63GIMX",
                 password: str = "BCyU3r4fbHZL4nfzxuUqV5VV3BVnEVSV5gnRFUvQEWUg"):
        """
        Initialize EmailUtils with SMTP configuration.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: AWS SES SMTP username
            password: AWS SES SMTP password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_email(self,
                  from_email: str,
                  to_emails: List[str],
                  subject: str,
                  body: str,
                  body_type: str = "html",
                  cc_emails: Optional[List[str]] = None,
                  bcc_emails: Optional[List[str]] = None,
                  attachments: Optional[List[str]] = None) -> bool:
        """
        Send an email via SMTP with AWS SES.
        
        Args:
            from_email: Sender email address
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: Type of body content ("html" or "plain")
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
            attachments: List of file paths to attach
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Add body
            if body_type.lower() == "html":
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # Prepare recipient list
            recipients = to_emails.copy()
            if cc_emails:
                recipients.extend(cc_emails)
            if bcc_emails:
                recipients.extend(bcc_emails)
            
            # Send email via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # Enable TLS
                server.starttls()
                
                # Authenticate with plain username and password
                server.login(self.username, self.password)
                
                # Send the message
                server.send_message(msg, from_email, recipients)
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def send_alert_email(self,
                        to_emails: List[str],
                        alert_type: str,
                        message: str,
                        metrics_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a formatted alert email with metrics data.
        
        Args:
            to_emails: List of recipient email addresses
            alert_type: Type of alert (e.g., "High Transaction Volume", "System Error")
            message: Alert message
            metrics_data: Optional dictionary containing metrics data
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"GasFree Alert: {alert_type}"
        
        # Create HTML body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; }}
                .alert-header {{ color: #856404; font-weight: bold; font-size: 18px; margin-bottom: 10px; }}
                .alert-message {{ color: #856404; margin-bottom: 15px; }}
                .metrics {{ background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; margin-top: 15px; }}
                .metrics h3 {{ margin-top: 0; color: #495057; }}
                .metric-row {{ display: flex; justify-content: space-between; margin-bottom: 5px; }}
                .metric-label {{ font-weight: bold; color: #495057; }}
                .metric-value {{ color: #6c757d; }}
                .timestamp {{ color: #6c757d; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <div class="alert-header">🚨 {alert_type}</div>
                <div class="alert-message">{message}</div>
            </div>
        """
        
        if metrics_data:
            html_body += '<div class="metrics"><h3>Metrics Data:</h3>'
            for key, value in metrics_data.items():
                html_body += f'<div class="metric-row"><span class="metric-label">{key}:</span><span class="metric-value">{value}</span></div>'
            html_body += '</div>'
        
        html_body += f"""
            <div class="timestamp">
                Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            from_email="no-reply@gasfree.io",
            to_emails=to_emails,
            subject=subject,
            body=html_body,
            body_type="html"
        )
    
    def send_daily_report(self,
                         to_emails: List[str],
                         report_data: Dict[str, Any]) -> bool:
        """
        Send a formatted daily report email.
        
        Args:
            to_emails: List of recipient email addresses
            report_data: Dictionary containing report data
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"GasFree Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Create HTML body for daily report
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
                .metric-section {{ margin-bottom: 20px; }}
                .metric-title {{ font-weight: bold; color: #495057; margin-bottom: 10px; }}
                .metric-value {{ font-size: 24px; color: #007bff; font-weight: bold; }}
                .timestamp {{ color: #6c757d; font-size: 12px; margin-top: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>GasFree Daily Report</h1>
                <p>Daily metrics and performance summary</p>
            </div>
            <div class="content">
        """
        
        for section, data in report_data.items():
            html_body += f'<div class="metric-section">'
            html_body += f'<div class="metric-title">{section}</div>'
            if isinstance(data, dict):
                for key, value in data.items():
                    html_body += f'<div class="metric-value">{key}: {value}</div>'
            else:
                html_body += f'<div class="metric-value">{data}</div>'
            html_body += '</div>'
        
        html_body += f"""
            </div>
            <div class="timestamp">
                Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            from_email="no-reply@gasfree.io",
            to_emails=to_emails,
            subject=subject,
            body=html_body,
            body_type="html"
        )


# Test the implementation
if __name__ == "__main__":
    print("EmailUtils - Simple SMTP Implementation")
    print("=" * 40)
    
    # Initialize email utils
    email_utils = EmailUtils()
    
    # Test sending email
    success = email_utils.send_email(
        from_email="no-reply@gasfree.io",
        to_emails=["kuangyuan1991@gmail.com"],
        subject="EmailUtils Test",
        body="This is a test email from the simple EmailUtils implementation.",
        body_type="plain"
    )
    
    if success:
        print("✅ Email sent successfully!")
    else:
        print("❌ Failed to send email") 