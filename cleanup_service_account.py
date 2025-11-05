#!/usr/bin/env python3
"""
cleanup_service_account.py
Removes the Gmail service account and its keys from the project.
"""
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

PROJECT_ID = input("Enter your Google Cloud Project ID: ").strip()
SA_NAME = "gmail-sender"
KEY_FILE = Path("gmail_service_account.json")

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

iam_service = build('iam', 'v1', credentials=creds)
sa_email = f"{SA_NAME}@{PROJECT_ID}.iam.gserviceaccount.com"

print(f"\nDeleting Service Account: {sa_email}")

try:
    iam_service.projects().serviceAccounts().delete(
        name=f"projects/{PROJECT_ID}/serviceAccounts/{sa_email}"
    ).execute()
    print(f"Service Account deleted: {sa_email}")
except HttpError as e:
    if e.resp.status == 404:
        print(f"Service Account not found: {sa_email}")
    else:
        print(f"Error deleting Service Account: {e}")
        exit(1)

if KEY_FILE.exists():
    KEY_FILE.unlink()
    print(f"Deleted local key file: {KEY_FILE}")
else:
    print(f"Key file not found: {KEY_FILE}")

print("\nCleanup complete.")
print("\nREMINDER: If you configured domain-wide delegation, remove it manually:")
print(f"   Go to: https://admin.google.com → Security → API Controls → Manage Domain-wide Delegation")
print(f"   Find and remove the client ID for: {sa_email}")
