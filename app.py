from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google_wrapper import GoogleCalendarWrapper
from logic.parse_and_sync_service import process_message

app = FastAPI()


class MessageIn(BaseModel):
    text: str


class MessageOut(BaseModel):
    kind: str
    name: Optional[str] = None
    date: Optional[str] = None
    action: Optional[str] = None
    event_id: Optional[str] = None


def build_calendar_wrapper() -> tuple[GoogleCalendarWrapper, str]:
    sa_path = os.getenv("SERVICE_ACCOUNT_FILE")
    calendar_id = os.getenv("CALENDAR_ID")
    tz = os.getenv("GCAL_TZ", "Asia/Jerusalem")
    if not sa_path or not calendar_id:
        raise RuntimeError("Missing SERVICE_ACCOUNT_FILE or CALENDAR_ID env var")
    creds = Credentials.from_service_account_file(sa_path, scopes=["https://www.googleapis.com/auth/calendar"])
    service = build("calendar", "v3", credentials=creds)
    return GoogleCalendarWrapper(service, calendar_id=calendar_id), tz


@app.post("/messages", response_model=MessageOut)
def receive_message(payload: MessageIn):
    try:
        wrapper, tz = build_calendar_wrapper()
        result = process_message(payload.text, wrapper, tz)
        return MessageOut(**{
            "kind": result.get("kind"),
            "name": result.get("name"),
            "date": str(result.get("date")),
            "action": result.get("action"),
            "event_id": result.get("event_id"),
        })
    except Exception as e:
        raise HTTPException(500, detail=str(e))
