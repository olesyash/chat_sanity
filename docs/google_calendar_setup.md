# Google Calendar Service Account Setup (AWS Lambda)

This guide explains how to connect your AWS Lambda to your personal Google Calendar using a Google Service Account (robotic account). No interactive user consent is required at runtime.

## Prerequisites
- A Google account (Gmail) that owns the target calendar.
- AWS account with Lambda + Secrets Manager permissions.
- Python runtime with `google-api-python-client` installed.

## 1) Create a Google Cloud Project and Enable Calendar API
1. Open https://console.cloud.google.com/
2. Create a new project (or select an existing one).
3. Go to APIs & Services → Library.
4. Search for "Google Calendar API" and click Enable.

## 2) Create a Service Account and Download Key
1. Go to IAM & Admin → Service Accounts.
2. Click Create Service Account.
3. Name it (e.g., `calendar-robot`) and create.
4. After creation, go to Keys → Add Key → Create new key → JSON.
5. Download the JSON (this is your private key). Keep it secure.

![alt text](image.png)

You will see a service account email like: `calendar-robot@<project-id>.iam.gserviceaccount.com`.

## 3) Share Your Calendar With the Service Account
1. Open Google Calendar (web) → Settings → Settings for my calendars.
2. Choose your calendar.
3. "Share with specific people or groups" → Add the service account email.
4. Permission: "Make changes to events".

Note your Calendar ID:
- For your primary calendar it’s usually your Gmail address (e.g., `you@gmail.com`).
- For other calendars, it might be found in the calendar’s settings under Integrate calendar.

## 4) Store the Service Account Key in AWS Secrets Manager
1. Open AWS Console → Secrets Manager → Store a new secret.
2. Secret type: Other type of secret.
3. Paste the entire JSON key content as the secret value.
4. Name it something like `gcal/service_account_json`.
5. Save and note the Secret ARN.

Security tips:
- Restrict IAM to least-privilege. Only Lambda role should access this secret.
- Do not log the secret.
- Consider rotating keys periodically; revoke immediately if compromised.

## 5) Build the Google Calendar Service in Lambda
Use the service account credentials to build the Calendar API client inside your Lambda.

```python
import json
import boto3
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SECRET_NAME = "gcal/service_account_json"  # adjust to your secret name
REGION_NAME = "us-east-1"  # adjust


def load_service_account_creds_from_secrets_manager():
    sm = boto3.client("secretsmanager", region_name=REGION_NAME)
    secret = sm.get_secret_value(SecretId=SECRET_NAME)
    key_json = secret.get("SecretString")
    if not key_json:
        raise RuntimeError("Service account secret not found or empty")
    data = json.loads(key_json)
    creds = Credentials.from_service_account_info(data, scopes=SCOPES)
    return creds


def build_calendar_service():
    creds = load_service_account_creds_from_secrets_manager()
    service = build("calendar", "v3", credentials=creds)
    return service
```

## 6) Use the Wrapper to Create/Update/Delete Events
Your repo includes `google_wrapper.GoogleCalendarWrapper` which expects a built `service` and a `calendar_id`.

```python
from datetime import datetime
from google_wrapper import GoogleCalendarWrapper
from agent import Event

service = build_calendar_service()
# Use your calendar ID, e.g., your gmail address or the calendar’s ID string
calendar_id = "your_email@gmail.com"

wrapper = GoogleCalendarWrapper(service, calendar_id=calendar_id)

# Create an event
evt = Event(kind="event", name="אסיפת הורים", description="אסיפת הורים",
            date=datetime(2025, 9, 10, 20, 0), location="School Hall")
new_event_id = wrapper.create_event(evt, duration_minutes=60, tz="Asia/Jerusalem")

# Update an event
wrapper.update_event(new_event_id, name="אסיפת הורים - עודכן", tz="Asia/Jerusalem")

# Delete an event
wrapper.delete_event(new_event_id)
```

## 7) Lambda Packaging and Environment
- Add `google-api-python-client` to your deployment package/layer.
- Ensure the Lambda role has `secretsmanager:GetSecretValue` for your secret ARN.
- Set `REGION_NAME`, `SECRET_NAME`, and `calendar_id` appropriately (env vars recommended).

## Troubleshooting
- 403 or Not Found:
  - Verify calendar was shared with the service account email with "Make changes to events".
  - Ensure you’re using the correct `calendar_id`.
- Time zones:
  - Pass a valid IANA timezone (e.g., `Asia/Jerusalem`).
  - Naive datetimes are treated as UTC (appends `Z`) while also setting `timeZone`.
- Quotas:
  - Monitor API quotas in Google Cloud Console if you do large volumes.

## Security Checklist
- Keep the service account JSON in Secrets Manager (never commit to git).
- Restrict IAM to least privilege.
- Limit scopes to only Calendar.
- Use a dedicated calendar for automation if possible.
- Rotate/recreate keys periodically and audit access.
