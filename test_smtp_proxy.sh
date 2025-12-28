#!/bin/bash
#
# test_smtp_proxy.sh
# Test sending email through the SMTP proxy
#
# Usage:
#   ./test_smtp_proxy.sh                           # Interactive mode
#   ./test_smtp_proxy.sh sender@domain.com recipient@example.com
#

set -e

# Default configuration
SMTP_HOST="${SMTP_HOST:-localhost}"
SMTP_PORT="${SMTP_PORT:-1025}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "============================================================"
echo "SMTP PROXY TEST"
echo "============================================================"
echo ""

# Get sender and recipient
if [ -n "$1" ] && [ -n "$2" ]; then
    SENDER="$1"
    RECIPIENT="$2"
else
    read -p "From (sender email): " SENDER
    read -p "To (recipient email): " RECIPIENT
fi

if [ -z "$SENDER" ] || [ -z "$RECIPIENT" ]; then
    echo -e "${RED}Error: Both sender and recipient are required${NC}"
    exit 1
fi

# Generate a unique subject with timestamp
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
SUBJECT="SMTP Proxy Test - $TIMESTAMP"

echo "Sending test email..."
echo "  From: $SENDER"
echo "  To: $RECIPIENT"
echo "  Subject: $SUBJECT"
echo "  Server: $SMTP_HOST:$SMTP_PORT"
echo ""

# Check if the proxy is running
if ! nc -z "$SMTP_HOST" "$SMTP_PORT" 2>/dev/null; then
    echo -e "${RED}Error: SMTP proxy is not running on $SMTP_HOST:$SMTP_PORT${NC}"
    echo ""
    echo "Start the proxy first with:"
    echo "  source .venv/bin/activate && python smtp_proxy.py"
    exit 1
fi

# Method 1: Try using Python (most reliable)
if command -v python3 &> /dev/null || command -v python &> /dev/null; then
    PYTHON_CMD=$(command -v python3 || command -v python)
    
    $PYTHON_CMD << EOF
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

msg = MIMEText("""Hello!

This is a test email sent through the SMTP proxy.

Sent at: ${TIMESTAMP}
From: ${SENDER}
To: ${RECIPIENT}

If you received this email, the SMTP proxy is working correctly!
""")

msg['Subject'] = '${SUBJECT}'
msg['From'] = '${SENDER}'
msg['To'] = '${RECIPIENT}'

try:
    server = smtplib.SMTP('${SMTP_HOST}', ${SMTP_PORT})
    server.sendmail('${SENDER}', ['${RECIPIENT}'], msg.as_string())
    server.quit()
    print('\033[0;32m✓ Email sent successfully!\033[0m')
except Exception as e:
    print(f'\033[0;31m✗ Failed to send email: {e}\033[0m')
    exit(1)
EOF

# Method 2: Fall back to swaks if Python fails
elif command -v swaks &> /dev/null; then
    echo "Using swaks..."
    swaks --to "$RECIPIENT" \
          --from "$SENDER" \
          --server "$SMTP_HOST:$SMTP_PORT" \
          --header "Subject: $SUBJECT" \
          --body "Hello!\n\nThis is a test email sent through the SMTP proxy.\n\nSent at: $TIMESTAMP"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Email sent successfully!${NC}"
    else
        echo -e "${RED}✗ Failed to send email${NC}"
        exit 1
    fi

# Method 3: Fall back to netcat/telnet raw SMTP
elif command -v nc &> /dev/null; then
    echo "Using netcat (raw SMTP)..."
    {
        sleep 0.5
        echo "HELO localhost"
        sleep 0.2
        echo "MAIL FROM:<$SENDER>"
        sleep 0.2
        echo "RCPT TO:<$RECIPIENT>"
        sleep 0.2
        echo "DATA"
        sleep 0.2
        echo "Subject: $SUBJECT"
        echo "From: $SENDER"
        echo "To: $RECIPIENT"
        echo ""
        echo "Hello! This is a test email sent through the SMTP proxy."
        echo "Sent at: $TIMESTAMP"
        echo "."
        sleep 0.2
        echo "QUIT"
    } | nc "$SMTP_HOST" "$SMTP_PORT"
    
    echo -e "${GREEN}✓ Email sent (check proxy logs for status)${NC}"

else
    echo -e "${RED}Error: No suitable SMTP client found${NC}"
    echo "Please install one of: python3, swaks, or netcat (nc)"
    exit 1
fi

echo ""
echo "============================================================"
echo "Check the SMTP proxy output to confirm the email was"
echo "forwarded to Gmail successfully."
echo "============================================================"
