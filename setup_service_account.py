#!/usr/bin/env python3
"""
setup_service_account.py
Creates a Gmail-capable service account and outputs client ID for domain-wide delegation.
"""
import base64
import json
from pathlib import Path
import warnings

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="You are using a Python version .*google\\.api_core.*",
)

import google.auth
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# === CONFIG ===
PROJECT_ID = input("Enter your Google Cloud Project ID: ").strip()
SA_NAME = "gmail-sender"
SA_DISPLAY_NAME = "Gmail Sender (Python Automation)"
KEY_FILE = Path("gmail_service_account.json")

# Scopes needed for IAM + Gmail
SCOPES = [
    'https://www.googleapis.com/auth/iam',
    'https://www.googleapis.com/auth/admin.directory.user.readonly'
]


def parse_error_info(error):
    try:
        payload = json.loads(error.content.decode("utf-8"))
    except Exception:
        return None

    details = payload.get("error", {}).get("details", [])
    for detail in details:
        if detail.get("@type") == "type.googleapis.com/google.rpc.ErrorInfo":
            return detail
    return None


def exit_with_service_enable_hint(service_name, project_id):
    console_url = f"https://console.developers.google.com/apis/api/{service_name}/overview?project={project_id}"
    print(f"Error: Required API '{service_name}' is disabled for project '{project_id}'.")
    print("Enable it with:")
    print(f"   gcloud services enable {service_name} --project {project_id}")
    print(f"Console link: {console_url}")
    exit(1)


def exit_with_permission_denied(project_id):
    print(f"Error: Permission denied while enabling required services for project '{project_id}'.")
    print("The active gcloud account lacks sufficient privileges (e.g., Service Usage Admin or Project Owner).")
    print("Check the active account: gcloud auth list")
    print(f"Ensure the account has permissions on project '{project_id}' or ask a project owner to enable the API.")
    exit(1)

print(f"\nUsing Google Cloud Project: {PROJECT_ID}")

try:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
except DefaultCredentialsError:
    print("Application Default Credentials not found. Run: gcloud auth application-default login")
    exit(1)

if creds.expired and creds.refresh_token:
    creds.refresh(Request())
if not creds.valid:
    print("Application Default Credentials are invalid. Run: gcloud auth application-default login")
    exit(1)

print("\nEnabling required APIs...")
serviceusage = build('serviceusage', 'v1', credentials=creds)
try:
    for api in ['iam.googleapis.com']:
        print(f"Enabling {api}...")
        serviceusage.services().enable(
            name=f"projects/{PROJECT_ID}/services/{api}"
        ).execute()
        print(f"Enabled {api}")
except HttpError as e:
    if e.resp.status == 403:
        console_url = f"https://console.developers.google.com/apis/api/iam.googleapis.com/overview?project={PROJECT_ID}"
        print(f"\nWarning: Cannot enable APIs automatically due to insufficient permissions.")
        print(f"Please enable the IAM API manually:")
        print(f"  1. Visit: {console_url}")
        print(f"  2. Click 'Enable API'")
        print(f"  3. Re-run this script\n")
        exit(1)
    print(f"Warning: Could not enable APIs automatically: {e}")
    print("You may need to enable them manually.")

print("\nCreating Service Account...")
iam_service = build('iam', 'v1', credentials=creds)

# 1. Create Service Account
sa_email = f"{SA_NAME}@{PROJECT_ID}.iam.gserviceaccount.com"
try:
    request = iam_service.projects().serviceAccounts().create(
        name=f"projects/{PROJECT_ID}",
        body={
            "accountId": SA_NAME,
            "serviceAccount": {
                "displayName": SA_DISPLAY_NAME
            }
        }
    )
    sa = request.execute()
    print(f"Service Account created: {sa['email']}")
except HttpError as e:
    info = parse_error_info(e)
    if info:
        reason = info.get("reason")
        metadata = info.get("metadata", {})
        if reason == "SERVICE_DISABLED":
            service_name = metadata.get("service", "iam.googleapis.com")
            exit_with_service_enable_hint(service_name, PROJECT_ID)
        if reason in {"AUTH_PERMISSION_DENIED", "SERVICE_PERMISSION_DENIED"}:
            exit_with_permission_denied(PROJECT_ID)
    if e.resp.status == 409 and "already exists" in str(e):
        print(f"Service Account already exists: {sa_email}")
    else:
        raise
except Exception as e:
    if "already exists" in str(e):
        print(f"Service Account already exists: {sa_email}")
    else:
        raise

# 2. Generate Key
try:
    key_request = iam_service.projects().serviceAccounts().keys().create(
        name=f"projects/{PROJECT_ID}/serviceAccounts/{sa_email}",
        body={}
    )
    key = key_request.execute()
    key_json = base64.b64decode(key["privateKeyData"]).decode("utf-8")
    key_data = json.loads(key_json)
    KEY_FILE.write_text(key_json)
    print(f"Private key saved: {KEY_FILE}")
except HttpError as e:
    info = parse_error_info(e)
    if info:
        reason = info.get("reason")
        metadata = info.get("metadata", {})
        if reason == "SERVICE_DISABLED":
            service_name = metadata.get("service", "iam.googleapis.com")
            exit_with_service_enable_hint(service_name, PROJECT_ID)
        if reason in {"AUTH_PERMISSION_DENIED", "SERVICE_PERMISSION_DENIED"}:
            exit_with_permission_denied(PROJECT_ID)
    print(f"Key generation failed: {e}")
    exit(1)
except Exception as e:
    print(f"Key generation failed: {e}")
    exit(1)

# 3. Extract Client ID
client_id = key_data['client_id']
print(f"\nCLIENT ID (copy this): {client_id}")
print(f"\nACTION REQUIRED:")
print(f"   Go to: https://admin.google.com → Security → API Controls → Manage Domain-wide Delegation")
print(f"   Click 'Add new' → Paste Client ID: {client_id}")
print(f"   Scopes: https://mail.google.com/")
print(f"   Save.")

print(f"\nSetup complete. Use send_email_sa.py next.")
