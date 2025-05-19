import os
from enum import Enum
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_session
from models import User

auth_router = APIRouter()


class ResponseUser(BaseModel):
    id: str
    email: str


class ReasonEnum(str, Enum):
    EMAIL = "email"


@auth_router.get("/auth/me", response_model=ResponseUser)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


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
            f"&redirect_uri={os.getenv('BASE_URL')}?reason={reason}"
            f"&scope={scope}"
        )
    }


@auth_router.get("/google_token_callback/{reason}")
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
        "redirect_uri": f"{os.getenv('BASE_URL')}?reason={reason}",
        "grant_type": "authorization_code",
    }
    token_response = requests.post(
        "https://www.googleapis.com/oauth2/v4/token",
        data=data,
        timeout=10,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response_json = token_response.json()

    if "access_token" not in response_json:
        return HTTPException(
            status_code=400,
            detail=f"Failed to get access token from Google, payload: {response_json}",
        )
    access_token = response_json["access_token"]
    await session.execute(
        current_user.update_config([reason, "token"], f"{access_token}")
    )
    await session.commit()
    return {"status": "ok"}
