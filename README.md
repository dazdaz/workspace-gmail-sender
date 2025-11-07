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

### Verify Domain-wide Delegation (Recommended First Step)

Before sending emails, verify your domain-wide delegation configuration:
```bash
python verify_delegation.py
```

This diagnostic tool will:
- Display your service account information (Client ID, project, etc.)
- Show the exact configuration steps needed for domain-wide delegation
- Test if delegation is properly configured
- Provide specific error diagnosis if there are issues

### Send an Email

The script supports both interactive and command-line modes:

#### Interactive Mode

Run without arguments for interactive prompts:
```bash
python send_email_sa.py
```

You'll be prompted for:
1. **Send as (email in domain)**: The email address of the user to impersonate (must be in your Google Workspace domain)
2. **Recipient**: The recipient's email address
3. **Subject**: Email subject line
4. **Body**: Email message body (supports multi-line input - press Ctrl-D on a new line when finished)

**Example Interactive Session:**
```
Send as (email in domain): user@yourdomain.com
Recipient: recipient@example.com
Subject: Test Email

Body (multi-line supported):
(Enter your message. Press Ctrl-D on a new line when finished)
Hello! This is a test email.

This is a multi-line message.
You can write as much as you want.
^D
```

#### Command-Line Mode

For automation or scripting, use command-line arguments:

```bash
# Basic usage
python send_email_sa.py -f sender@domain.com -t recipient@example.com -s "Subject" -b "Body"

# Long form
python send_email_sa.py --from sender@domain.com --to recipient@example.com --subject "Test" --body "Message"

# With optional parameters (subject and body default if omitted)
python send_email_sa.py -f sender@domain.com -t recipient@example.com
```

**Command-Line Arguments:**
- `-f, --from EMAIL`: Sender email address (required in CLI mode)
- `-t, --to EMAIL`: Recipient email address (required in CLI mode)
- `-s, --subject TEXT`: Email subject line (optional, defaults to "Test from Service Account")
- `-b, --body TEXT`: Email body text (optional, defaults to standard message)
- `--body-file FILE`: Read email body from a text file (cannot be used with `-b`)

**Using body from a file:**
```bash
# Create a message file
echo "Hello,

This is a multi-line email message.
It can contain as much text as needed.

Best regards" > message.txt

# Send email with body from file
python send_email_sa.py -f sender@domain.com -t recipient@example.com -s "Subject" --body-file message.txt
```

**For help:**
```bash
python send_email_sa.py --help
```

## File Structure

```
├── send_email_sa.py          # Main script for sending emails
├── setup_service_account.py  # Setup script for creating service account
├── verify_delegation.py      # Diagnostic tool to verify delegation config
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

**"Gmail API has not been used in project [PROJECT_ID] before or it is disabled"**
- The Gmail API needs to be enabled for your project
- Enable it with: `gcloud services enable gmail.googleapis.com --project=YOUR_PROJECT_ID`
- Or visit the console link provided in the error message
- Wait a few minutes after enabling, then try again
- The enhanced error handling in `send_email_sa.py` will automatically detect this and provide the exact command

**"invalid_grant: Invalid email or User ID"**
- This means domain-wide delegation is NOT configured correctly
- Run `python verify_delegation.py` to diagnose the issue
- Verify the Client ID (from your service account) is added to domain-wide delegation in Google Admin Console
- Ensure the OAuth scope `https://mail.google.com/` is authorized
- Confirm the user you're impersonating exists in your Workspace domain
- Check that the domain matches your Workspace primary domain
- See "Domain-wide Delegation Configuration" section below for detailed steps

**"Failed to send: Insufficient Permission"**
- Verify domain-wide delegation is properly configured in Google Admin Console
- Check that the Client ID matches exactly
- Ensure the scope `https://mail.google.com/` is authorized
- Confirm you are using a Google Workspace account, not regular Gmail

**"FutureWarning: You are using a Python version..."**
- This warning has been suppressed in the updated code
- If you still see it, ensure you're using the latest version of `send_email_sa.py`
- The warning filter is applied before importing Google libraries

**"Warning: No ADC found"**
- Run `gcloud auth application-default login` to set up application default credentials

**"Service Account already exists"**
- This is normal if you've run the setup before
- The script will continue and generate a new key

### Domain-wide Delegation Configuration

If you're getting `invalid_grant` errors, follow these steps carefully:

1. **Get your Client ID**
   - Run `python verify_delegation.py` to see your service account's Client ID
   - Or find it in your `gmail_service_account.json` file

2. **Configure in Google Admin Console**
   - Go to: https://admin.google.com/ac/owl/domainwidedelegation
   - Navigate to **Security** → **API Controls** → **Manage Domain-wide Delegation**
   - Click **"Add new"**
   - Enter your Client ID
   - Add OAuth scope: `https://mail.google.com/`
   - Click **"Authorize"**

3. **Wait and Verify**
   - Changes may take 5-10 minutes to propagate
   - Run `python verify_delegation.py` to test the configuration
   - The diagnostic tool will confirm if delegation is working

4. **Important Notes**
   - The user you're impersonating MUST exist in your Google Workspace domain
   - The email domain must match your Workspace primary domain
   - You need Google Workspace admin privileges to configure delegation
   - Regular Gmail accounts (@gmail.com) will NOT work

### Permission Errors

If you encounter permission errors:
1. Verify your Google Cloud Project has the necessary APIs enabled (Gmail API, IAM API)
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
