#!/usr/bin/env python3
"""
Script to send a test email from no-reply@gasfree.io to kuangyuan1991@gmail.com
"""

from email_utils import EmailUtils
from datetime import datetime


def send_test_email():
    """Send a test email to kuangyuan1991@gmail.com"""
    print("Sending test email...")
    print("=" * 40)
    
    # Initialize email utils
    email_utils = EmailUtils()
    
    # Email configuration
    from_email = "no-reply@gasfree.io"
    to_email = "kuangyuan1991@gmail.com"
    subject = "GasFree Alert Bot - Test Email"
    
    # Test email body
    body = f"""
    Hello!
    
    This is a test email from the GasFree Alert Bot system.
    
    Test Details:
    - Sent from: {from_email}
    - Sent to: {to_email}
    - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
    - Purpose: Testing EmailUtils functionality
    
    If you receive this email, it means the EmailUtils class is working correctly
    with the AWS SES configuration.
    
    Best regards,
    GasFree Alert Bot Team
    """
    
    print(f"From: {from_email}")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Send the email
    success = email_utils.send_email(
        from_email=from_email,
        to_emails=[to_email],
        subject=subject,
        body=body,
        body_type="plain"
    )
    
    if success:
        print("✅ Test email sent successfully!")
        print("📧 Please check your inbox at kuangyuan1991@gmail.com")
    else:
        print("❌ Failed to send test email")
        print("Please check the error messages above for details")
    
    return success


def send_test_alert_email():
    """Send a test alert email with metrics"""
    print("\nSending test alert email...")
    print("=" * 40)
    
    email_utils = EmailUtils()
    
    # Test metrics data
    metrics_data = {
        "Test Transaction Count": "1,234",
        "Test Total Amount": "$45,678",
        "Test Active Users": "567",
        "Test Status": "Working"
    }
    
    success = email_utils.send_alert_email(
        to_emails=["kuangyuan1991@gmail.com"],
        alert_type="EmailUtils Test Alert",
        message="This is a test alert to verify the EmailUtils functionality is working correctly with the new authentication credentials.",
        metrics_data=metrics_data
    )
    
    if success:
        print("✅ Test alert email sent successfully!")
        print("📧 Please check your inbox for the formatted alert email")
    else:
        print("❌ Failed to send test alert email")
    
    return success


if __name__ == "__main__":
    print("GasFree Alert Bot - Email Test")
    print("=" * 50)
    
    # Send basic test email
    basic_success = send_test_email()
    
    # Send alert test email
    alert_success = send_test_alert_email()
    
    print("\n" + "=" * 50)
    if basic_success and alert_success:
        print("🎉 All test emails sent successfully!")
        print("📧 Check kuangyuan1991@gmail.com for both emails")
    elif basic_success:
        print("✅ Basic test email sent, but alert email failed")
    elif alert_success:
        print("✅ Alert test email sent, but basic email failed")
    else:
        print("❌ Both test emails failed")
    
    print("\nTest completed!") 