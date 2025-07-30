import base64
import logging
from dataclasses import dataclass
from typing import Any, AsyncContextManager, Callable, Dict, List, Optional, Type

from bs4 import BeautifulSoup
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
class EmailMessage:  # pylint: disable=too-many-instance-attributes
    id: str
    thread_id: str
    subject: Optional[str]
    sender: Optional[str]
    recipient: Optional[str]
    date: Optional[str]
    body: str
    snippet: str
    labels: List[str]


class GmailToolkit(BaseToolkit):

    session_factory: Callable[[], AsyncContextManager[AsyncSession]]
    client_id: str
    client_secret: str

    def get_tools(self) -> List[BaseTool]:
        return [
            GmailReadUnreadTool(
                session_factory=self.session_factory,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
        ]


class EmptyInput(BaseModel):
    pass


class GmailReadUnreadTool(GoogleBaseTool):
    name: str = "gmail_read_unread"
    description: str = "Read unread emails from Gmail"
    args_schema: Type[BaseModel] = EmptyInput

    async def _arun(self, config: RunnableConfig) -> List[EmailMessage]:
        credentials = self._create_credentials(
            await self._get_user(config), "https://mail.google.com/", "email"
        )
        service = build("gmail", "v1", credentials=credentials)
        results = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread in:inbox", maxResults=100)
            .execute()
        )

        messages = results.get("messages", [])

        if not messages:
            logger.info("No unread messages found")
            return []

        unread_emails = []

        for message in messages:
            msg = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )

            email_data = self._extract_email_data(msg)
            unread_emails.append(email_data)

        logger.info("Retrieved %d unread emails", len(unread_emails))
        return unread_emails

    def _extract_email_data(self, message: Dict[str, Any]) -> EmailMessage:
        headers = message["payload"].get("headers", [])

        subject = self._get_header_value(headers, "Subject")
        sender = self._get_header_value(headers, "From")
        recipient = self._get_header_value(headers, "To")
        date = self._get_header_value(headers, "Date")

        body = self._extract_message_body(message["payload"])

        return EmailMessage(
            id=message["id"],
            thread_id=message["threadId"],
            subject=subject,
            sender=sender,
            recipient=recipient,
            date=date,
            body=body,
            snippet=message.get("snippet", ""),
            labels=message.get("labelIds", []),
        )

    def _get_header_value(
        self, headers: List[Dict[str, str]], name: str
    ) -> Optional[str]:
        for header in headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return None

    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        body = ""

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
                        break
                elif part["mimeType"] == "text/html" and not body:
                    if "data" in part["body"]:
                        html_body = base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8")
                        body = BeautifulSoup(html_body, "html.parser").get_text(
                            strip=True
                        )
        elif payload["mimeType"] == "text/plain":
            if "data" in payload["body"]:
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        elif payload["mimeType"] == "text/html":
            if "data" in payload["body"]:
                html_body = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                    "utf-8"
                )
                body = BeautifulSoup(html_body, "html.parser").get_text(strip=True)

        return body
