# Gmail Workspace Service Account Email Sender

A Python application for sending emails via Gmail Workspace using Google Service Accounts with domain-wide delegation. This tool allows you to impersonate any user in your Google Workspace domain to send emails programmatically.

**Note**: This tool is specifically designed for Gmail Workspace (Google Workspace) accounts and requires domain-wide delegation configuration. It will not work with regular consumer Gmail accounts.

## Features

- Send emails using service account authentication
- Domain-wide delegation support for impersonating users in your Google Workspace domain
- Simple command-line interface
- No user interaction required after initial setup
- Secure credential management

## Prerequisites

- Google Cloud Project with Gmail API enabled (you will provide its **project ID** when running the setup script)
- IAM API enabled for that project (the script will attempt to enable it automatically if needed)
- **Google Workspace domain** (formerly G Suite) with admin privileges
- **This tool does NOT work with regular Gmail accounts**
- Python 3.6 or higher
- `gcloud` CLI tool installed and authenticated
- Service account with appropriate IAM permissions

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup Process

### 1. Configure Google Cloud Project

Make sure you know the exact **project ID** (not just the project name). Confirm the active project with `gcloud config get-value project` or set it explicitly via `gcloud config set project <PROJECT_ID>` before proceeding.

1. Create a new Google Cloud Project or use an existing one
2. Enable the Gmail API:
   ```bash
   gcloud services enable gmail.googleapis.com
   ```
3. Enable the IAM API:
   ```bash
   gcloud services enable iam.googleapis.com
   ```

### 2. Authenticate with Google Cloud

Set up application default credentials:
```bash
gcloud auth application-default login
```

### 3. Create Service Account

Run the setup script to create a service account and generate credentials:
```bash
python setup_service_account.py
```

You'll be prompted for:
- Your Google Cloud Project ID (the same ID you verified in Step 1; e.g. the output of `gcloud config get-value project`)
- The script will create a service account named `gmail-sender`
- A private key file `gmail_service_account.json` will be generated

### 4. Configure Domain-wide Delegation

1. Go to [Google Admin Console](https://admin.google.com)
2. Navigate to **Security** → **API Controls** → **Manage Domain-wide Delegation**
3. Click **Add new**
4. Enter the Client ID from the setup script output
5. Add the scope: `https://mail.google.com/`
6. Click **Authorize**

## Usage

### Send an Email

Run the email sending script:
```bash
python send_email_sa.py
```

You'll be prompted for:
1. **Send as (email in domain)**: The email address of the user to impersonate (must be in your Google Workspace domain)
2. **Recipient**: The recipient's email address
3. **Subject**: Email subject line
4. **Body**: Email message body

### Example Session
```
Send as (email in domain): user@yourdomain.com
Recipient: recipient@example.com
Subject: Test Email
Body: Hello! This is a test email sent via service account.
```

## File Structure

```
├── send_email_sa.py          # Main script for sending emails
├── setup_service_account.py  # Setup script for creating service account
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── gmail_service_account.json # Generated service account key (created during setup)
```

## Important Notes

### Google Workspace vs Regular Gmail
- **This tool requires Google Workspace** (formerly G Suite)
- **Will not work with regular Gmail accounts** (@gmail.com)
- Requires domain-wide delegation which is only available in Google Workspace
- The impersonated user must be part of your Google Workspace domain

## Security Considerations

- **Keep credentials secure**: The `gmail_service_account.json` file contains sensitive private key information
- **Limit permissions**: Only grant necessary scopes to the service account
- **Monitor usage**: Regularly review Gmail usage logs for unusual activity
- **Rotate keys**: Periodically regenerate service account keys
- **Access control**: Ensure only authorized personnel can access the service account

## Troubleshooting

### Common Issues

**"Error: gmail_service_account.json not found"**
- Run `setup_service_account.py` first to generate the credentials file

**"Failed to send: Insufficient Permission"**
- Verify domain-wide delegation is properly configured in Google Admin Console
- Check that the Client ID matches exactly
- Ensure the scope `https://mail.google.com/` is authorized
- Confirm you are using a Google Workspace account, not regular Gmail

**"Warning: No ADC found"**
- Run `gcloud auth application-default login` to set up application default credentials

**"Service Account already exists"**
- This is normal if you've run the setup before
- The script will continue and generate a new key

### Permission Errors

If you encounter permission errors:
1. Verify your Google Cloud Project has the necessary APIs enabled
2. Check that your Google Workspace admin account has sufficient privileges
3. Ensure the service account has the correct IAM roles
4. Confirm you are using a Google Workspace domain, not a regular Gmail account
5. Confirm the active gcloud account has rights to enable services (e.g., **Service Usage Admin** or **Project Owner**) when running `gcloud services enable`

## Dependencies

- `google-auth==2.23.4` - Google authentication library
- `google-auth-oauthlib==1.1.0` - OAuth library for Google Auth
- `google-auth-httplib2==0.2.0` - HTTP transport library for Google Auth
- `google-api-python-client==2.108.0` - Google API client library

## License

This project is provided as-is for educational and operational purposes. Ensure compliance with your organization's security policies and Google's Terms of Service when using this tool.

## Support

For issues related to:
- **Google Cloud Setup**: Refer to [Google Cloud Documentation](https://cloud.google.com/docs)
- **Gmail API**: Refer to [Gmail API Documentation](https://developers.google.com/gmail/api)
- **Domain-wide Delegation**: Refer to [Google Workspace Admin Help](https://support.google.com/a/answer/162106)
- **Google Workspace**: Refer to [Google Workspace Admin Help Center](https://support.google.com/a/answer/2464515)
