#!/usr/bin/env python3
"""
send_email_sa.py
Send email via Service Account with domain-wide delegation.
Impersonates any user in the domain.
"""
import base64
import os
import sys
import warnings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText

# Suppress FutureWarning about Python version
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core._python_version_support")

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
    
    # Get body
    body = input("Body: ").strip() or "Hello! This email was sent via Service Account + Domain-Wide Delegation."
    
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
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"\n✓ SUCCESS! Email sent successfully!")
        print(f"Message ID: {result['id']}")
        print(f"{'='*50}")
        return True
        
    except Exception as e:
        print(f"\n✗ FAILED to send email: {e}")
        
        # Provide helpful troubleshooting hints
        if "insufficient_permission" in str(e).lower() or "permission" in str(e).lower():
            print("\n" + "="*60)
            print("TROUBLESHOOTING TIPS:")
            print("="*60)
            print("1. Verify domain-wide delegation is configured in Google Admin Console")
            print("2. Check that the Client ID was added with scope: https://mail.google.com/")
            print("3. Ensure the impersonate user exists in your Google Workspace domain")
            print("4. Confirm you have admin privileges in your Google Workspace domain")
            print("="*60)
        elif "invalid_grant" in str(e).lower():
            print("\n" + "="*60)
            print("TROUBLESHOOTING TIPS:")
            print("="*60)
            print("1. The impersonate user email might be incorrect")
            print("2. The user must exist in your Google Workspace domain")
            print("3. Domain-wide delegation might not be properly configured")
            print("="*60)
        
        return False

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("GMAIL WORKSPACE SERVICE ACCOUNT EMAIL SENDER")
    print("="*60)
    
    # Check credentials
    if not check_credentials():
        sys.exit(1)
    
    # Get user input
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
