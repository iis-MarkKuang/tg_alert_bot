# EmailUtils Class Documentation

The `EmailUtils` class provides a comprehensive solution for sending emails via SMTP with AWS SES support. It includes features for sending basic emails, alert emails, daily reports, and emails with attachments.

## Features

- ✅ SMTP email sending with AWS SES support
- ✅ HTML and plain text email support
- ✅ Email attachments
- ✅ CC and BCC recipients
- ✅ Pre-formatted alert emails with metrics
- ✅ Pre-formatted daily report emails
- ✅ Automatic SMTP password generation for AWS SES
- ✅ Error handling and logging

## Installation

The EmailUtils class uses only Python standard library modules, so no additional dependencies are required beyond what's already in your project.

## Configuration

### AWS SES Setup

The class is configured to work with AWS SES. You'll need:

1. **AWS SES SMTP credentials**:
   - SMTP Username: Your AWS SES SMTP username
   - Secret Access Key: Your AWS secret access key
   - Region: AWS region (default: us-east-1)

2. **SMTP Server**: `email-smtp.us-east-1.amazonaws.com`
3. **SMTP Port**: `587` (TLS)

### Environment Variables (Recommended)

For security, consider using environment variables for sensitive credentials:

```bash
export AWS_SES_USERNAME="your_smtp_username"
export AWS_SECRET_ACCESS_KEY="your_secret_access_key"
export AWS_REGION="us-east-1"
```

## Usage

### Basic Email Sending

```python
from email_utils import EmailUtils

# Initialize with default AWS SES settings
email_utils = EmailUtils()

# Send a simple email
success = email_utils.send_email(
    from_email="no-reply@gasfree.io",
    to_emails=["admin@gasfree.com"],
    subject="Test Email",
    body="This is a test email.",
    body_type="plain"  # or "html"
)

if success:
    print("Email sent successfully!")
else:
    print("Failed to send email.")
```

### HTML Email

```python
html_body = """
<html>
<body>
    <h1>GasFree Alert</h1>
    <p>This is an <strong>HTML formatted</strong> email.</p>
    <ul>
        <li>Feature 1</li>
        <li>Feature 2</li>
    </ul>
</body>
</html>
"""

success = email_utils.send_email(
    from_email="no-reply@gasfree.io",
    to_emails=["admin@gasfree.com"],
    subject="HTML Email",
    body=html_body,
    body_type="html"
)
```

### Alert Email with Metrics

```python
metrics_data = {
    "Transaction Count": "1,234",
    "Total Amount": "$45,678",
    "Active Users": "567",
    "Error Rate": "0.5%"
}

success = email_utils.send_alert_email(
    to_emails=["admin@gasfree.com", "ops@gasfree.com"],
    alert_type="High Transaction Volume",
    message="Transaction volume has exceeded normal thresholds.",
    metrics_data=metrics_data
)
```

### Daily Report Email

```python
report_data = {
    "Daily Transactions": {
        "Total Count": "12,345",
        "Total Amount": "$234,567",
        "Success Rate": "99.8%"
    },
    "User Activity": {
        "Active Users": "1,234",
        "New Users": "56"
    }
}

success = email_utils.send_daily_report(
    to_emails=["reports@gasfree.com"],
    report_data=report_data
)
```

### Email with Attachments

```python
success = email_utils.send_email(
    from_email="no-reply@gasfree.io",
    to_emails=["admin@gasfree.com"],
    subject="Report with Attachments",
    body="Please find the attached report.",
    body_type="plain",
    attachments=["/path/to/report.pdf", "/path/to/data.csv"]
)
```

### Email with CC and BCC

```python
success = email_utils.send_email(
    from_email="no-reply@gasfree.io",
    to_emails=["primary@gasfree.com"],
    subject="System Update",
    body="System maintenance completed.",
    body_type="plain",
    cc_emails=["team@gasfree.com"],
    bcc_emails=["archive@gasfree.com"]
)
```

## Class Methods

### `__init__(smtp_server, smtp_port, username, secret_access_key, aws_region)`

Initialize the EmailUtils class with SMTP configuration.

**Parameters:**
- `smtp_server` (str): SMTP server address (default: AWS SES)
- `smtp_port` (int): SMTP server port (default: 587)
- `username` (str): AWS SES SMTP username
- `secret_access_key` (str): AWS secret access key
- `aws_region` (str): AWS region (default: us-east-1)

### `send_email(from_email, to_emails, subject, body, body_type, cc_emails, bcc_emails, attachments)`

Send a basic email via SMTP.

**Parameters:**
- `from_email` (str): Sender email address
- `to_emails` (List[str]): List of recipient email addresses
- `subject` (str): Email subject
- `body` (str): Email body content
- `body_type` (str): Type of body content ("html" or "plain")
- `cc_emails` (Optional[List[str]]): List of CC email addresses
- `bcc_emails` (Optional[List[str]]): List of BCC email addresses
- `attachments` (Optional[List[str]]): List of file paths to attach

**Returns:** bool - True if email sent successfully, False otherwise

### `send_alert_email(to_emails, alert_type, message, metrics_data)`

Send a formatted alert email with metrics data.

**Parameters:**
- `to_emails` (List[str]): List of recipient email addresses
- `alert_type` (str): Type of alert (e.g., "High Transaction Volume")
- `message` (str): Alert message
- `metrics_data` (Optional[Dict[str, Any]]): Optional dictionary containing metrics data

**Returns:** bool - True if email sent successfully, False otherwise

### `send_daily_report(to_emails, report_data)`

Send a formatted daily report email.

**Parameters:**
- `to_emails` (List[str]): List of recipient email addresses
- `report_data` (Dict[str, Any]): Dictionary containing report data

**Returns:** bool - True if email sent successfully, False otherwise

## Error Handling

The class includes comprehensive error handling:

- SMTP connection errors
- Authentication failures
- File attachment errors
- Invalid email addresses
- Network timeouts

All methods return a boolean indicating success/failure and print error messages for debugging.

## Security Considerations

1. **Credentials**: Store AWS credentials securely using environment variables
2. **Email Validation**: Validate email addresses before sending
3. **Rate Limiting**: Be aware of AWS SES sending limits
4. **Attachment Security**: Validate file types and sizes before attaching

## Testing

Run the example script to test the email functionality:

```bash
cd v2
python email_example.py
```

## Integration with Existing Code

The EmailUtils class can be easily integrated with your existing alert bot:

```python
from email_utils import EmailUtils
from db_operations import get_psql_conn, query_trx

# Initialize email utils
email_utils = EmailUtils()

# Get transaction data
conn = get_psql_conn()
trx_count = query_trx(conn, start_time, end_time, 'count')

# Send alert if threshold exceeded
if trx_count > 1000:
    email_utils.send_alert_email(
        to_emails=["admin@gasfree.com"],
        alert_type="High Transaction Volume",
        message=f"Transaction count ({trx_count}) exceeded threshold.",
        metrics_data={"Transaction Count": str(trx_count)}
    )
```

## Troubleshooting

### Common Issues

1. **Authentication Error**: Check AWS credentials and SMTP username
2. **Connection Timeout**: Verify SMTP server and port settings
3. **Email Not Delivered**: Check sender email verification in AWS SES
4. **Attachment Errors**: Ensure file paths exist and are readable

### Debug Mode

Enable debug output by modifying the SMTP connection:

```python
with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
    server.set_debuglevel(1)  # Enable debug output
    server.starttls()
    server.login(self.username, smtp_password)
    server.send_message(msg, from_email, recipients)
``` 