from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger
from agent import route_and_parse, Event
from google_wrapper import GoogleCalendarWrapper


SEARCH_WINDOW_MINUTES = 120


def _time_bounds(dt: datetime) -> tuple[str, str]:
    start = dt - timedelta(minutes=SEARCH_WINDOW_MINUTES)
    end = dt + timedelta(minutes=SEARCH_WINDOW_MINUTES)
    return start.isoformat() + "Z", end.isoformat() + "Z"


def find_existing_event(wrapper: GoogleCalendarWrapper, name: str, when: datetime) -> Optional[str]:
    try:
        time_min, time_max = _time_bounds(when)
        events = (
            wrapper.service.events()
            .list(
                calendarId=wrapper.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                q=name,
            )
            .execute()
        )
        for item in events.get("items", []):
            if not item.get("summary"):
                continue
            if name in item["summary"] or item["summary"] in name:
                return item.get("id")
    except Exception as e:
        logger.info("find_existing_event: list failed: {}", e)
    return None


def sync_event(event: Event, wrapper: GoogleCalendarWrapper, tz: str) -> Dict[str, Any]:
    existing_id = find_existing_event(wrapper, event.name, event.date)
    if existing_id:
        updated = wrapper.update_event(
            existing_id,
            name=event.name,
            description=event.description,
            location=event.location,
            start=event.date,
            end=event.date + timedelta(minutes=60),
            tz=tz,
        )
        return {"action": "updated", "event_id": updated.get("id", existing_id)}
    new_id = wrapper.create_event(event, duration_minutes=60, tz=tz)
    return {"action": "created", "event_id": new_id}


def process_message(text: str, wrapper: GoogleCalendarWrapper, tz: str) -> Dict[str, Any]:
    parsed = route_and_parse(text)
    result: Dict[str, Any] = {
        "kind": getattr(parsed, "kind", "other"),
        "name": getattr(parsed, "name", None),
        "date": getattr(parsed, "date", None),
    }
    if getattr(parsed, "kind", None) == "event":
        sync = sync_event(parsed, wrapper, tz)
        result.update(sync)
    return result
