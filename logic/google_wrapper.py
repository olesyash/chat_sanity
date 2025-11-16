from typing import Any, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loguru import logger
from agent import Event


class GoogleCalendarWrapper:
    def __init__(self, service: Any, calendar_id: str = "primary") -> None:
        self.service = service
        self.calendar_id = calendar_id

    def _rfc3339(self, dt: datetime, tz: str = "UTC") -> dict:
        if dt.tzinfo is None:
            try:
                dt = dt.replace(tzinfo=ZoneInfo(tz))
            except Exception:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return {"dateTime": dt.isoformat(), "timeZone": tz}

    def _event_body(self, e: Event, duration_minutes: int = 60, tz: str = "UTC") -> dict:
        start = e.date
        end = start + timedelta(minutes=duration_minutes)
        body = {
            "summary": e.name or "",
            "description": e.description or "",
            "location": e.location or "",
            "start": self._rfc3339(start, tz),
            "end": self._rfc3339(end, tz),
        }
        return body

    def create_event(self, e: Event, duration_minutes: int = 60, tz: str = "UTC") -> str:
        body = self._event_body(e, duration_minutes=duration_minutes, tz=tz)
        logger.info("google calendar: creating event name='{}' date={} tz={}", e.name, e.date, tz)
        created = (
            self.service.events()
            .insert(calendarId=self.calendar_id, body=body)
            .execute()
        )
        return created.get("id")

    def update_event(
        self,
        event_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        tz: str = "UTC",
    ) -> dict:
        current = self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()
        if name is not None:
            current["summary"] = name
        if description is not None:
            current["description"] = description
        if location is not None:
            current["location"] = location
        if start is not None:
            current["start"] = self._rfc3339(start, tz)
        if end is not None:
            current["end"] = self._rfc3339(end, tz)
        logger.info("google calendar: updating event id={} name='{}'", event_id, current.get("summary"))
        updated = (
            self.service.events()
            .update(calendarId=self.calendar_id, eventId=event_id, body=current)
            .execute()
        )
        return updated

    def delete_event(self, event_id: str) -> None:
        logger.info("google calendar: deleting event id={}", event_id)
        self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
        return None

