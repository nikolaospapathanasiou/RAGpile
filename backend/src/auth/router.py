import os
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

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
