import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, AsyncContextManager, Callable, Dict, List, Optional, Type

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from src.tools.base import GoogleBaseTool

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    id: str
    summary: str
    description: Optional[str]
    start: Optional[str]
    end: Optional[str]
    location: Optional[str]
    attendees: List[str]
    created: Optional[str]
    updated: Optional[str]


class GoogleCalendarToolkit(BaseToolkit):

    session_factory: Callable[[], AsyncContextManager[AsyncSession]]
    client_id: str
    client_secret: str

    def get_tools(self) -> List[BaseTool]:
        return [
            CalendarListEventsTool(
                session_factory=self.session_factory,
                client_id=self.client_id,
                client_secret=self.client_secret,
            ),
            CalendarCreateEventTool(
                session_factory=self.session_factory,
                client_id=self.client_id,
                client_secret=self.client_secret,
            ),
        ]


class EmptyInput(BaseModel):
    pass


class CreateEventInput(BaseModel):
    summary: str
    description: Optional[str] = None
    start_datetime: str
    end_datetime: str
    location: Optional[str] = None
    attendees: Optional[List[str]] = None


class CalendarListEventsTool(GoogleBaseTool):
    name: str = "calendar_list_events"
    description: str = "List upcoming calendar events from Google Calendar"
    args_schema: Type[BaseModel] = EmptyInput

    async def _arun(self, config: RunnableConfig) -> List[CalendarEvent]:
        credentials = self._create_credentials(
            await self._get_user(config),
            "https://www.googleapis.com/auth/calendar.events",
            "calendar",
        )
        service = build("calendar", "v3", credentials=credentials)

        now = datetime.utcnow().isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=50,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        if not events:
            logger.info("No upcoming events found")
            return []

        calendar_events = []
        for event in events:
            event_data = self._extract_event_data(event)
            calendar_events.append(event_data)

        logger.info("Retrieved %d upcoming events", len(calendar_events))
        return calendar_events

    def _extract_event_data(self, event: Dict[str, Any]) -> CalendarEvent:
        start = event.get("start", {})
        end = event.get("end", {})

        start_time = start.get("dateTime") or start.get("date")
        end_time = end.get("dateTime") or end.get("date")

        attendees = []
        if "attendees" in event:
            attendees = [attendee.get("email", "") for attendee in event["attendees"]]

        return CalendarEvent(
            id=event.get("id", ""),
            summary=event.get("summary", ""),
            description=event.get("description"),
            start=start_time,
            end=end_time,
            location=event.get("location"),
            attendees=attendees,
            created=event.get("created"),
            updated=event.get("updated"),
        )


class CalendarCreateEventTool(GoogleBaseTool):
    name: str = "calendar_create_event"
    description: str = "Create a new event in Google Calendar"
    args_schema: Type[BaseModel] = CreateEventInput

    async def _arun(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        description: Optional[str],
        location: Optional[str],
        attendees: Optional[List[str]],
        config: RunnableConfig,
    ) -> CalendarEvent:
        credentials = self._create_credentials(
            await self._get_user(config),
            "https://www.googleapis.com/auth/calendar.events",
            "calendar",
        )
        service = build("calendar", "v3", credentials=credentials)

        event_body = {
            "summary": summary,
            "start": {"dateTime": start_datetime, "timeZone": "UTC"},
            "end": {"dateTime": end_datetime, "timeZone": "UTC"},
        }

        if description:
            event_body["description"] = description

        if location:
            event_body["location"] = location

        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        try:
            created_event = (
                service.events().insert(calendarId="primary", body=event_body).execute()
            )

            event_data = self._extract_event_data(created_event)
            logger.info("Created calendar event: %s", summary)
            return event_data

        except Exception as e:
            logger.error("Error creating calendar event '%s': %s", summary, str(e))
            raise

    def _extract_event_data(self, event: Dict[str, Any]) -> CalendarEvent:
        start = event.get("start", {})
        end = event.get("end", {})

        start_time = start.get("dateTime") or start.get("date")
        end_time = end.get("dateTime") or end.get("date")

        attendees = []
        if "attendees" in event:
            attendees = [attendee.get("email", "") for attendee in event["attendees"]]

        return CalendarEvent(
            id=event.get("id", ""),
            summary=event.get("summary", ""),
            description=event.get("description"),
            start=start_time,
            end=end_time,
            location=event.get("location"),
            attendees=attendees,
            created=event.get("created"),
            updated=event.get("updated"),
        )
