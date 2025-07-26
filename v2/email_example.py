#!/usr/bin/env python3
"""
Example usage of EmailUtils class for sending different types of emails.
"""

from email_utils import EmailUtils
from datetime import datetime


def example_basic_email():
    """Example of sending a basic email."""
    email_utils = EmailUtils()
    
    success = email_utils.send_email(
        from_email="no-reply@gasfree.io",
        to_emails=["kuangyuan1991@gmail.com"],
        subject="Test Basic Email",
        body="This is a simple test email from the GasFree Alert Bot.",
        body_type="plain"
    )
    
    print(f"Basic email sent: {'Success' if success else 'Failed'}")


def example_html_email():
    """Example of sending an HTML formatted email."""
    email_utils = EmailUtils()
    
    html_body = """
    <html>
    <body>
        <h1>GasFree Alert</h1>
        <p>This is an <strong>HTML formatted</strong> email.</p>
        <ul>
            <li>Feature 1</li>
            <li>Feature 2</li>
            <li>Feature 3</li>
        </ul>
    </body>
    </html>
    """
    
    success = email_utils.send_email(
        from_email="no-reply@gasfree.io",
        to_emails=["kuangyuan1991@gmail.com"],
        subject="Test HTML Email",
        body=html_body,
        body_type="html"
    )
    
    print(f"HTML email sent: {'Success' if success else 'Failed'}")


def example_alert_email():
    """Example of sending an alert email with metrics data."""
    email_utils = EmailUtils()
    
    metrics_data = {
        "Transaction Count": "1,234",
        "Total Amount": "$45,678",
        "Active Users": "567",
        "Error Rate": "0.5%"
    }
    
    success = email_utils.send_alert_email(
        to_emails=["kuangyuan1991@gmail.com"],
        alert_type="High Transaction Volume",
        message="Transaction volume has exceeded normal thresholds. Please review system performance.",
        metrics_data=metrics_data
    )
    
    print(f"Alert email sent: {'Success' if success else 'Failed'}")


def example_daily_report():
    """Example of sending a daily report email."""
    email_utils = EmailUtils()
    
    report_data = {
        "Daily Transactions": {
            "Total Count": "12,345",
            "Total Amount": "$234,567",
            "Success Rate": "99.8%"
        },
        "User Activity": {
            "Active Users": "1,234",
            "New Users": "56",
            "Retention Rate": "85%"
        },
        "System Performance": {
            "Uptime": "99.9%",
            "Average Response Time": "120ms",
            "Error Rate": "0.1%"
        }
    }
    
    success = email_utils.send_daily_report(
        to_emails=["kuangyuan1991@gmail.com"],
        report_data=report_data
    )
    
    print(f"Daily report sent: {'Success' if success else 'Failed'}")


def example_email_with_attachments():
    """Example of sending an email with attachments."""
    email_utils = EmailUtils()
    
    # Note: You would need actual files to attach
    # attachments = ["/path/to/report.pdf", "/path/to/data.csv"]
    attachments = []  # Empty for this example
    
    success = email_utils.send_email(
        from_email="no-reply@gasfree.io",
        to_emails=["kuangyuan1991@gmail.com"],
        subject="Monthly Report with Attachments",
        body="Please find the attached monthly report.",
        body_type="plain",
        attachments=attachments
    )
    
    print(f"Email with attachments sent: {'Success' if success else 'Failed'}")


def example_email_with_cc_bcc():
    """Example of sending an email with CC and BCC recipients."""
    email_utils = EmailUtils()
    
    success = email_utils.send_email(
        from_email="no-reply@gasfree.io",
        to_emails=["kuangyuan1991@gmail.com"],
        subject="System Update",
        body="System maintenance completed successfully.",
        body_type="plain",
        cc_emails=["admin@gasfree.io"],
        bcc_emails=["archive@gasfree.io"]
    )
    
    print(f"Email with CC/BCC sent: {'Success' if success else 'Failed'}")


if __name__ == "__main__":
    print("EmailUtils Examples")
    print("=" * 50)
    
    # Run examples
    example_basic_email()
    example_html_email()
    example_alert_email()
    example_daily_report()
    example_email_with_attachments()
    example_email_with_cc_bcc()
    
    print("\nAll examples completed!") 