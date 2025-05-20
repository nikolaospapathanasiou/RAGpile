import os
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_session
from models import User

auth_router = APIRouter()


class ResponseApp(BaseModel):
    name: str
    token_expiry: int
    refresh_token_expiry: int

    @classmethod
    def from_config(cls, key, config):
        return cls(
            name=key,
            token_expiry=config.get("token_expiry", 0),
            refresh_token_expiry=config.get("refresh_token_expiry", 0),
        )


class ResponseUser(BaseModel):
    id: str
    email: str
    apps: dict[str, ResponseApp]

    @classmethod
    def from_user(cls, user: User) -> "ResponseUser":
        return cls(
            id=user.id,
            email=user.email,
            apps={
                key: ResponseApp.from_config(key, user.config[key])
                for key in user.config.keys()
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

    current_user.config[reason.value] = current_user.config.get(reason.value, {})
    current_user.config[reason.value]["token"] = access_token
    current_user.config[reason.value]["token_expiry"] = (
        utc_timestamp + response_json["expires_in"]
    )
    current_user.config[reason.value]["refresh_token"] = refresh_token
    current_user.config[reason.value]["refresh_token_expiry"] = (
        utc_timestamp + response_json["refresh_token_expires_in"]
    )
    await session.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(config=current_user.config)
    )
    await session.commit()
    return ResponseUser.from_user(current_user)
