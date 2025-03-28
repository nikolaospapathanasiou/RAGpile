import os
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.token import TokenManager, remove_current_user, set_current_user
from dependencies import get_current_user, get_session, get_token_manager
from models import User

auth_router = APIRouter()


class ResponseUser(BaseModel):
    id: str
    email: str


@auth_router.get("/auth/me", response_model=ResponseUser)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@auth_router.post("/auth/logout")
async def logout(response: Response):
    remove_current_user(response)
    response.status_code = 204


@auth_router.get("/auth/google_login")
async def login():
    return {
        "auth_url": (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code"
            f"&client_id={os.getenv('GOOGLE_CLIENT_ID')}"
            f"&redirect_uri={os.getenv('BASE_URL')}"
            f"&scope=https://www.googleapis.com/auth/userinfo.email"
        )
    }


@auth_router.get("/auth/google_callback", response_model=ResponseUser)
async def callback(
    code: str,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    token_manager: Annotated[TokenManager, Depends(get_token_manager)],
):
    data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("BASE_URL"),
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

    user_info_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    user_info = user_info_response.json()
    user = session.query(User).get(user_info["id"])
    if not user:
        user = User(id=user_info["id"], email=user_info["email"])
        session.add(user)
        session.commit()
    set_current_user(response, token_manager, user.id)
    return user
