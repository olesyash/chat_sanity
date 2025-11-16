# run_once_local.py
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
from google_wrapper import GoogleCalendarWrapper
from agent import Event
from dotenv import load_dotenv
import os

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
CALENDAR_ID = os.getenv("CALENDAR_ID")

SCOPES = ["https://www.googleapis.com/auth/calendar"]


creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("calendar", "v3", credentials=creds)

gc = GoogleCalendarWrapper(service, calendar_id=CALENDAR_ID)

evt = Event(kind="event", name="אסיפת הורים", description="אסיפת הורים",
            date=datetime(2025, 9, 10, 20, 0), location="School Hall", original_message="test")

event_id = gc.create_event(evt, duration_minutes=60, tz="Asia/Jerusalem")
print("Created event:", event_id)

gc.update_event(event_id, name="אסיפת הורים - עודכן", tz="Asia/Jerusalem")
# gc.delete_event(event_id)

