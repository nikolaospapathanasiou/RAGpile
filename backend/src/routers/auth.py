import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Union

import requests  # type: ignore
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_session, get_telegram_application_token
from models import User

auth_router = APIRouter()
logger = logging.getLogger(__name__)


class ResponseIntegration(BaseModel):
    name: str
    active: bool


class ResponseUser(BaseModel):
    id: str
    email: str
    integrations: dict[str, ResponseIntegration]

    @classmethod
    def from_user(cls, user: User) -> "ResponseUser":
        return cls(
            id=user.id,
            email=user.email,
            integrations={
                name: ResponseIntegration(
                    name=name, active=user.has_active_integration(name)
                )
                for name in user.integrations.keys()
            },
        )


class ReasonEnum(str, Enum):
    EMAIL = "email"


@auth_router.get("/auth/me", response_model=ResponseUser)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return ResponseUser.from_user(current_user)


@auth_router.get("/google_token/{reason}")
async def new_token(reason: ReasonEnum):
    if reason == ReasonEnum.EMAIL:
        scope = "https://mail.google.com/"
    else:
        raise HTTPException(status_code=400, detail="Invalid reason")
    return {
        "auth_url": (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code"
            f"&client_id={os.getenv('GOOGLE_CLIENT_ID')}"
            f"&redirect_uri={os.getenv('BASE_URL')}/ragpile/?reason={reason.value}"
            f"&scope={scope}"
            "&access_type=offline"
            "&prompt=consent"
        )
    }


@auth_router.post("/google_token_callback/{reason}")
async def callback(
    current_user: Annotated[User, Depends(get_current_user)],
    reason: ReasonEnum,
    code: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": f"{os.getenv('BASE_URL')}/ragpile/?reason={reason.value}",
        "grant_type": "authorization_code",
        "access_type": "offline",
    }
    print(data)
    token_response = requests.post(
        "https://www.googleapis.com/oauth2/v4/token",
        data=data,
        timeout=10,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response_json = token_response.json()
    print(response_json)
    if "access_token" not in response_json:
        return HTTPException(
            status_code=400,
            detail=f"Failed to get access token from Google, payload: {response_json}",
        )
    access_token = response_json["access_token"]
    refresh_token = response_json["refresh_token"]
    utc_now = datetime.now(timezone.utc)
    utc_timestamp = int(utc_now.timestamp())

    current_user.integrations[reason.value] = current_user.integrations.get(
        reason.value, {}
    )
    current_user.integrations[reason.value]["token"] = access_token
    current_user.integrations[reason.value]["token_expiry"] = str(
        utc_timestamp + response_json["expires_in"]
    )
    current_user.integrations[reason.value]["refresh_token"] = refresh_token
    current_user.integrations[reason.value]["refresh_token_expiry"] = str(
        utc_timestamp + response_json["refresh_token_expires_in"]
    )
    await session.execute(User.update_integrations(current_user))
    session.expunge(current_user)
    await session.commit()

    return ResponseUser.from_user(current_user)


@auth_router.post("/telegram_callback")
async def telegram_callback(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    data: dict[str, Union[str, int]],
    telegram_application_token: Annotated[str, Depends(get_telegram_application_token)],
):
    if "hash" not in data:
        raise HTTPException(
            status_code=400,
            detail="hash key not found in the telegram callback payload",
        )

    if "id" not in data:
        raise HTTPException(
            status_code=400, detail="id key not found in the telegram callback payload"
        )

    prehash_value = "\n".join(
        f"{key}={data[key]}" for key in sorted(data.keys()) if key != "hash"
    )
    logger.info("telegram prehash value %s", prehash_value)
    secret_key = hashlib.sha256(telegram_application_token.encode("utf-8")).digest()
    expected_hash = hmac.new(
        secret_key, prehash_value.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if expected_hash != data["hash"]:
        logger.warning(
            "telegram hash mismatch expected: %s, received: %s",
            expected_hash,
            data["hash"],
        )
        raise HTTPException(status_code=403, detail="the hash failed validation")
    current_user.integrations["telegram"] = current_user.integrations.get(
        "telegram", {}
    )
    current_user.integrations["telegram"]["user_id"] = str(data["id"])
    await session.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(integrations=current_user.integrations)
    )
    session.expunge(current_user)
    await session.commit()
    return ResponseUser.from_user(current_user)
