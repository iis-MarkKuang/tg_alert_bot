#!/usr/bin/env python3
"""
Test script to verify EmailUtils authentication with the new credentials.
"""

from email_utils import EmailUtils
import os


def test_email_authentication():
    """Test email authentication with the new credentials."""
    print("Testing EmailUtils Authentication")
    print("=" * 40)
    
    # Initialize email utils with the new credentials
    email_utils = EmailUtils()
    
    print(f"SMTP Server: {email_utils.smtp_server}")
    print(f"SMTP Port: {email_utils.smtp_port}")
    print(f"Username: {email_utils.username}")
    print(f"AWS Region: {email_utils.aws_region}")
    print(f"From Email: no-reply@gasfree.io")
    print()
    
    # Test SMTP password generation
    try:
        smtp_password = email_utils._generate_smtp_password()
        print(f"✅ SMTP Password generated successfully (length: {len(smtp_password)})")
    except Exception as e:
        print(f"❌ Failed to generate SMTP password: {e}")
        return False
    
    # Test a simple email (replace with actual test email)
    test_recipient = os.getenv("TEST_EMAIL", "test@example.com")
    
    print(f"\nSending test email to: {test_recipient}")
    print("Note: Set TEST_EMAIL environment variable to test with real email")
    
    success = email_utils.send_email(
        from_email="no-reply@gasfree.io",
        to_emails=[test_recipient],
        subject="EmailUtils Authentication Test",
        body="This is a test email to verify EmailUtils authentication is working correctly.",
        body_type="plain"
    )
    
    if success:
        print("✅ Email sent successfully!")
        return True
    else:
        print("❌ Failed to send email")
        return False


def test_alert_email():
    """Test alert email functionality."""
    print("\nTesting Alert Email")
    print("=" * 20)
    
    email_utils = EmailUtils()
    test_recipient = os.getenv("TEST_EMAIL", "test@example.com")
    
    metrics_data = {
        "Test Metric 1": "Value 1",
        "Test Metric 2": "Value 2",
        "Status": "Testing"
    }
    
    success = email_utils.send_alert_email(
        to_emails=[test_recipient],
        alert_type="Authentication Test",
        message="This is a test alert to verify the EmailUtils authentication.",
        metrics_data=metrics_data
    )
    
    if success:
        print("✅ Alert email sent successfully!")
    else:
        print("❌ Failed to send alert email")
    
    return success


if __name__ == "__main__":
    print("EmailUtils Authentication Test")
    print("=" * 50)
    
    # Test basic authentication
    auth_success = test_email_authentication()
    
    # Test alert email
    alert_success = test_alert_email()
    
    print("\n" + "=" * 50)
    if auth_success and alert_success:
        print("🎉 All tests passed! EmailUtils is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    print("\nTo test with a real email address, set the TEST_EMAIL environment variable:")
    print("export TEST_EMAIL=your-email@example.com")
    print("python test_email_auth.py") 