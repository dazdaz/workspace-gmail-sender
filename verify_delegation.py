#!/usr/bin/env python3
"""
verify_delegation.py
Verify domain-wide delegation configuration for Gmail service account.
"""
import json
import warnings

# Suppress FutureWarning about Python version
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core._python_version_support")

from google.oauth2 import service_account

KEY_FILE = "gmail_service_account.json"
SCOPES = ['https://mail.google.com/']

print("\n" + "="*70)
print("DOMAIN-WIDE DELEGATION VERIFICATION")
print("="*70)

# Read the service account file
with open(KEY_FILE, 'r') as f:
    sa_data = json.load(f)

print("\nService Account Information:")
print("-" * 70)
print(f"Project ID:     {sa_data['project_id']}")
print(f"Client Email:   {sa_data['client_email']}")
print(f"Client ID:      {sa_data['client_id']}")

print("\n" + "="*70)
print("CONFIGURATION STEPS REQUIRED")
print("="*70)

print("\n1. Go to Google Admin Console:")
print("   https://admin.google.com/ac/owl/domainwidedelegation")
print("   (Or: Security → API Controls → Domain-wide delegation)")

print("\n2. Click 'Add new' (or 'Manage Domain Wide Delegation')")

print("\n3. Add these details:")
print(f"   Client ID:    {sa_data['client_id']}")
print(f"   OAuth Scopes: https://mail.google.com/")

print("\n4. Click 'Authorize'")

print("\n" + "="*70)
print("IMPORTANT NOTES")
print("="*70)
print("\n• The user you're impersonating MUST exist in your Workspace domain")
print("• The user's email domain must match your Workspace primary domain")
print("• You must have admin access to configure domain-wide delegation")
print("• Changes may take a few minutes to propagate")

print("\n" + "="*70)
print("VERIFICATION TEST")
print("="*70)

test_email = input("\nEnter a test email from your domain to impersonate: ").strip()

if test_email:
    try:
        print(f"\nAttempting to create delegated credentials for: {test_email}")
        credentials = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=SCOPES
        )
        delegated_credentials = credentials.with_subject(test_email)
        
        # Try to refresh the token (this will fail if delegation isn't configured)
        from google.auth.transport.requests import Request
        delegated_credentials.refresh(Request())
        
        print("✓ SUCCESS! Domain-wide delegation is working correctly!")
        print(f"✓ The service account can impersonate: {test_email}")
        
    except Exception as e:
        error_str = str(e)
        print(f"\n✗ FAILED: {error_str}")
        
        if "invalid_grant" in error_str.lower():
            print("\n" + "="*70)
            print("DIAGNOSIS: Domain-wide delegation is NOT configured")
            print("="*70)
            print("\nThis error means one of the following:")
            print(f"  • Client ID {sa_data['client_id']} is not added to domain-wide delegation")
            print(f"  • The OAuth scope https://mail.google.com/ is not authorized")
            print(f"  • The user '{test_email}' doesn't exist in your Workspace domain")
            print(f"  • The domain doesn't match your Workspace primary domain")
            print("\nPlease follow the configuration steps above.")
        else:
            print(f"\nUnexpected error: {e}")

print("\n" + "="*70)
