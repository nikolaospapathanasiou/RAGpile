import os

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_session
from models import User

auth_router = APIRouter(
    prefix="/auth",
)


@auth_router.get("/google_login")
async def login():
    return {
        "auth_url": (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code"
            f"&client_id={os.getenv('GOOGLE_CLIENT_ID')}"
            f"&redirect_uri={os.getenv('FRONTEND_URL')}"
            f"&scope=https://www.googleapis.com/auth/userinfo.email"
        )
    }


@auth_router.get("/auth/google_callback")
async def callback(code: str, session: Session = Depends(get_session)):
    data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("FRONTEND_URL"),
        "grant_type": "authorization_code",
    }
    response = requests.post(
        "https://www.googleapis.com/oauth2/v4/token",
        data=data,
        timeout=10,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response_json = response.json()

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
        session.add(User(id=user_info["id"], email=user_info["email"]))
        session.commit()
    return {"user": user_info}
