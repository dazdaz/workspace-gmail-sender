#!/usr/bin/env python3
"""
smtp_proxy.py
SMTP Proxy Server for Gmail Workspace

Listens for SMTP connections on localhost and forwards emails to Gmail
using a Service Account with domain-wide delegation.

Usage:
    python smtp_proxy.py                    # Default port 1025
    python smtp_proxy.py --port 2525        # Custom port
    python smtp_proxy.py --domain myco.com  # Restrict sender domain
"""
import argparse
import asyncio
import base64
import os
import sys
import signal
import warnings
from email import message_from_bytes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Suppress FutureWarning about Python version
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core._python_version_support")

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as SMTPServer, Envelope, Session
from google.oauth2 import service_account
from googleapiclient.discovery import build

# === CONFIG ===
KEY_FILE = "gmail_service_account.json"
SCOPES = ['https://mail.google.com/']
DEFAULT_PORT = 1025
DEFAULT_HOST = "127.0.0.1"


class GmailSMTPHandler:
    """SMTP handler that forwards emails via Gmail API"""
    
    def __init__(self, allowed_domain=None):
        self.allowed_domain = allowed_domain
        self._credentials = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Load service account credentials"""
        if not os.path.exists(KEY_FILE):
            print(f"ERROR: {KEY_FILE} not found!")
            print("Run setup_service_account.py first.")
            sys.exit(1)
        
        self._credentials = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=SCOPES
        )
        print(f"✓ Loaded service account credentials from {KEY_FILE}")
    
    def _validate_sender(self, sender_email):
        """Validate sender email is in allowed domain"""
        if not self.allowed_domain:
            return True
        
        domain = sender_email.split('@')[-1].lower()
        return domain == self.allowed_domain.lower()
    
    def _send_via_gmail(self, sender, recipients, message_data):
        """Send email via Gmail API"""
        try:
            # Create delegated credentials to impersonate the sender
            delegated_credentials = self._credentials.with_subject(sender)
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=delegated_credentials, cache_discovery=False)
            
            # The message_data is already a complete email, just base64 encode it
            raw_message = base64.urlsafe_b64encode(message_data).decode('utf-8')
            
            # Send the email
            result = service.users().messages().send(
                userId=sender,
                body={'raw': raw_message}
            ).execute()
            
            return True, result.get('id', 'unknown')
            
        except Exception as e:
            return False, str(e)
    
    async def handle_exception(self, error):
        """Silently handle exceptions for malformed/unrecognised commands (e.g., HTTP requests)"""
        # Ignore HTTP requests hitting SMTP port - don't log them
        pass
    
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        """Handle RCPT TO command"""
        envelope.rcpt_tos.append(address)
        return '250 OK'
    
    async def handle_DATA(self, server, session, envelope: Envelope):
        """Handle DATA command - forward email via Gmail API"""
        sender = envelope.mail_from
        recipients = envelope.rcpt_tos
        message_data = envelope.content
        
        # Validate sender domain
        if not self._validate_sender(sender):
            error_msg = f"Sender domain not allowed: {sender}"
            print(f"✗ REJECTED: {error_msg}")
            return f'550 {error_msg}'
        
        print(f"\n{'─'*50}")
        print(f"📧 Incoming email")
        print(f"   From: {sender}")
        print(f"   To: {', '.join(recipients)}")
        
        # Parse message to get subject for logging
        try:
            msg = message_from_bytes(message_data)
            subject = msg.get('Subject', '(no subject)')
            print(f"   Subject: {subject}")
        except:
            pass
        
        # Send via Gmail API
        success, result = self._send_via_gmail(sender, recipients, message_data)
        
        if success:
            print(f"   ✓ Sent successfully (Message ID: {result})")
            return '250 Message accepted for delivery'
        else:
            print(f"   ✗ Failed: {result}")
            return f'550 Failed to send: {result}'


class QuietSMTP(SMTPServer):
    """Custom SMTP server that suppresses unrecognised command logging"""
    async def smtp_UNRECOGNISED(self, arg):
        """Silently handle unrecognised commands (like HTTP POST hitting SMTP port)"""
        # Don't print anything, just return error to client
        return '500 Command not recognised'


class QuietController(Controller):
    """Custom Controller that uses QuietSMTP to suppress unrecognised command logs"""
    def factory(self):
        return QuietSMTP(self.handler)


def run_server(host, port, allowed_domain=None):
    """Start the SMTP proxy server"""
    handler = GmailSMTPHandler(allowed_domain=allowed_domain)
    
    controller = QuietController(
        handler,
        hostname=host,
        port=port,
        ready_timeout=10
    )
    
    print(f"\n{'='*60}")
    print("SMTP PROXY FOR GMAIL WORKSPACE")
    print("="*60)
    print(f"\n✓ Listening on {host}:{port}")
    if allowed_domain:
        print(f"✓ Restricted to domain: {allowed_domain}")
    else:
        print("⚠ No domain restriction (any sender in your Workspace)")
    print(f"\nReady to accept SMTP connections...")
    print(f"Press Ctrl+C to stop\n")
    print("─"*60)
    
    controller.start()
    
    # Handle graceful shutdown
    shutdown_requested = False
    
    def shutdown(signum, frame):
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        print(f"\n\nShutting down...")
        controller.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # Keep running - use new_event_loop() to avoid deprecation warning
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if not shutdown_requested:
            controller.stop()


def main():
    parser = argparse.ArgumentParser(
        description='SMTP Proxy for Gmail Workspace using Service Account',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Start proxy on default port (1025):
    python smtp_proxy.py

  Start proxy on custom port:
    python smtp_proxy.py --port 2525

  Restrict to specific domain:
    python smtp_proxy.py --domain dazdaz.org

  Test with swaks:
    swaks --to recipient@example.com --from sender@yourdomain.com \\
          --server localhost:1025 --body "Test message"

  Test with Python:
    import smtplib
    server = smtplib.SMTP('localhost', 1025)
    server.sendmail('sender@yourdomain.com', ['recipient@example.com'], 
                    'Subject: Test\\n\\nHello!')
    server.quit()
        """
    )
    
    parser.add_argument(
        '--host',
        default=DEFAULT_HOST,
        help=f'Host to bind to (default: {DEFAULT_HOST})'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=DEFAULT_PORT,
        help=f'Port to listen on (default: {DEFAULT_PORT})'
    )
    
    parser.add_argument(
        '--domain', '-d',
        help='Restrict senders to this domain (e.g., yourdomain.com)'
    )
    
    args = parser.parse_args()
    
    run_server(args.host, args.port, args.domain)


if __name__ == "__main__":
    main()
