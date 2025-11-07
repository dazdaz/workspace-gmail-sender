#!/usr/bin/env python3
"""
send_email_sa.py
Send email via Service Account with domain-wide delegation.
Impersonates any user in the domain.

Usage:
    Interactive mode:
        python send_email_sa.py
    
    Command-line mode:
        python send_email_sa.py -f sender@domain.com -t recipient@example.com -s "Subject" -b "Body"
        python send_email_sa.py --from sender@domain.com --to recipient@example.com --subject "Test" --body "Message"
"""
import argparse
import base64
import os
import sys
import warnings

# Suppress FutureWarning about Python version - MUST be before google imports
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core._python_version_support")

from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText

# === CONFIG ===
KEY_FILE = "gmail_service_account.json"
SCOPES = ['https://mail.google.com/']

def check_credentials():
    """Check if service account credentials file exists"""
    if not os.path.exists(KEY_FILE):
        print(f"\n{'='*60}")
        print(f"ERROR: {KEY_FILE} not found!")
        print(f"{'='*60}")
        print(f"\nPlease run setup_service_account.py first to create the credentials file.")
        print(f"\nCommand: python setup_service_account.py")
        print(f"{'='*60}")
        return False
    return True

def get_multiline_input(prompt):
    """Get multi-line input from user, terminated by Ctrl-D (EOF)"""
    print(prompt)
    print("(Enter your message. Press Ctrl-D on a new line when finished)")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    return '\n'.join(lines)

def get_user_input():
    """Get user input with validation"""
    print("\n" + "="*50)
    print("EMAIL CONFIGURATION")
    print("="*50)
    
    # Get impersonate user
    impersonate_user = input("\nSend as (email in domain): ").strip()
    if not impersonate_user:
        print("Error: Email address is required!")
        return None, None, None, None
    
    # Get recipient
    recipient = input("Recipient: ").strip()
    if not recipient:
        print("Error: Recipient email is required!")
        return None, None, None, None
    
    # Get subject
    subject = input("Subject: ").strip() or "Test from Service Account"
    
    # Get body - multi-line input
    print("\nBody (multi-line supported):")
    body = get_multiline_input("")
    if not body.strip():
        body = "Hello! This email was sent via Service Account + Domain-Wide Delegation."
    
    return impersonate_user, recipient, subject, body

def send_email(impersonate_user, recipient, subject, body):
    """Send email using service account"""
    try:
        print(f"\n{'='*50}")
        print("SENDING EMAIL")
        print("="*50)
        print(f"From: {impersonate_user}")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        
        # Load service account and impersonate user
        print("\nLoading service account credentials...")
        credentials = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=SCOPES
        )
        delegated_credentials = credentials.with_subject(impersonate_user)
        print("✓ Credentials loaded successfully")
        
        # Build Gmail service
        print("Connecting to Gmail API...")
        service = build('gmail', 'v1', credentials=delegated_credentials)
        print("✓ Gmail service initialized")
        
        # Create message
        print("Creating email message...")
        message = MIMEText(body)
        message['to'] = recipient
        message['from'] = impersonate_user
        message['subject'] = subject
        
        # Encode and send
        print("Sending email...")
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId=impersonate_user,
            body={'raw': raw_message}
        ).execute()
        
        print(f"\n✓ SUCCESS! Email sent successfully!")
        print(f"Message ID: {result['id']}")
        print(f"{'='*50}")
        return True
        
    except Exception as e:
        print(f"\n✗ FAILED to send email: {e}")
        
        # Provide helpful troubleshooting hints
        error_str = str(e).lower()
        
        if "api has not been used" in error_str or "accessnotconfigured" in error_str:
            # Extract project ID from error if possible
            import re
            project_match = re.search(r'project (\d+)', str(e))
            project_id = project_match.group(1) if project_match else "YOUR_PROJECT_ID"
            
            print("\n" + "="*60)
            print("TROUBLESHOOTING: Gmail API Not Enabled")
            print("="*60)
            print(f"The Gmail API needs to be enabled for project {project_id}")
            print("\nEnable it with:")
            print(f"  gcloud services enable gmail.googleapis.com --project={project_id}")
            print("\nOr visit:")
            print(f"  https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project={project_id}")
            print("\nWait a few minutes after enabling, then try again.")
            print("="*60)
        elif "insufficient_permission" in error_str or "permission" in error_str:
            print("\n" + "="*60)
            print("TROUBLESHOOTING TIPS:")
            print("="*60)
            print("1. Verify domain-wide delegation is configured in Google Admin Console")
            print("2. Check that the Client ID was added with scope: https://mail.google.com/")
            print("3. Ensure the impersonate user exists in your Google Workspace domain")
            print("4. Confirm you have admin privileges in your Google Workspace domain")
            print("="*60)
        elif "invalid_grant" in error_str:
            print("\n" + "="*60)
            print("TROUBLESHOOTING TIPS:")
            print("="*60)
            print("1. The impersonate user email might be incorrect")
            print("2. The user must exist in your Google Workspace domain")
            print("3. Domain-wide delegation might not be properly configured")
            print("4. Run: python verify_delegation.py to diagnose")
            print("="*60)
        
        return False

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Send email via Gmail Workspace using Service Account with domain-wide delegation.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode:
    python send_email_sa.py

  Command-line mode:
    python send_email_sa.py -f sender@domain.com -t recipient@example.com -s "Subject" -b "Body"
    python send_email_sa.py --from sender@domain.com --to recipient@example.com --subject "Test" --body "Message"
        """
    )
    
    parser.add_argument(
        '-f', '--from',
        dest='sender',
        metavar='EMAIL',
        help='Sender email address (user to impersonate in your domain)'
    )
    
    parser.add_argument(
        '-t', '--to',
        dest='recipient',
        metavar='EMAIL',
        help='Recipient email address'
    )
    
    parser.add_argument(
        '-s', '--subject',
        metavar='TEXT',
        help='Email subject line'
    )
    
    parser.add_argument(
        '-b', '--body',
        metavar='TEXT',
        help='Email body text'
    )
    
    return parser.parse_args()

def main():
    """Main execution function"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Check credentials
    if not check_credentials():
        sys.exit(1)
    
    # Determine if using command-line mode or interactive mode
    if args.sender or args.recipient or args.subject or args.body:
        # Command-line mode: at least one argument provided
        # Validate that all required arguments are present
        if not args.sender:
            print("Error: --from is required when using command-line mode")
            sys.exit(1)
        if not args.recipient:
            print("Error: --to is required when using command-line mode")
            sys.exit(1)
        
        impersonate_user = args.sender
        recipient = args.recipient
        subject = args.subject or "Test from Service Account"
        body = args.body or "Hello! This email was sent via Service Account + Domain-Wide Delegation."
        
        print("\n" + "="*60)
        print("GMAIL WORKSPACE SERVICE ACCOUNT EMAIL SENDER")
        print("="*60)
        print("\nCommand-line mode")
    else:
        # Interactive mode: no arguments provided
        print("\n" + "="*60)
        print("GMAIL WORKSPACE SERVICE ACCOUNT EMAIL SENDER")
        print("="*60)
        
        user_data = get_user_input()
        if not user_data[0]:  # If impersonate_user is None
            print("\nCancelled. Please provide valid input.")
            sys.exit(1)
        
        impersonate_user, recipient, subject, body = user_data
    
    # Send email
    success = send_email(impersonate_user, recipient, subject, body)
    
    if success:
        print(f"\nEmail sent successfully from {impersonate_user} to {recipient}")
    else:
        print(f"\nFailed to send email. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
