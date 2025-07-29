import datetime
from calendar import timegm
from typing import Annotated, AsyncIterator, Awaitable, Callable

import jwt
from fastapi import Cookie, Depends, HTTPException, Response
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from models import User


class Token:
    def __init__(self, user_id: str, exp: int | None = None):
        if not exp:
            self.exp = timegm(
                (
                    datetime.datetime.now(tz=datetime.timezone.utc)
                    + datetime.timedelta(hours=1)
                ).timetuple()
            )
        else:
            self.exp = exp
        self.user_id = user_id

    def expires_soon(self) -> bool:
        return self.exp < timegm(
            (
                datetime.datetime.now(tz=datetime.timezone.utc)
                + datetime.timedelta(minutes=10)
            ).timetuple()
        )

    def payload(self) -> dict:
        return {"user_id": self.user_id, "exp": self.exp}


class TokenManager:
    def __init__(self, secret: str):
        self.secret = secret

    def sign_token(self, token: Token) -> str:
        return jwt.encode(
            token.payload(),
            self.secret,
            algorithm="HS256",
        )

    def decode_token(self, token: str) -> Token:
        decoded = jwt.decode(token, self.secret, algorithms=["HS256"])
        return Token(user_id=decoded["id"], exp=decoded.get("exp"))


def get_current_user_factory(
    token_manager: TokenManager, get_session: Callable[[], AsyncIterator[AsyncSession]]
) -> Callable[[Response, AsyncSession, str | None], Awaitable[User]]:
    async def _get_current_user(
        response: Response,
        session: Annotated[AsyncSession, Depends(get_session)],
        token: Annotated[str | None, Cookie(optional=True)] = None,
    ) -> User:
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            token_decoded = token_manager.decode_token(token)
        except PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Not authenticated") from exc

        if token_decoded.expires_soon():
            set_current_user(response, token_manager, token_decoded.user_id)

        user = await session.get(User, token_decoded.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user

    return _get_current_user


def set_current_user(
    response: Response, token_manager: TokenManager, user_id: str
) -> None:
    token = token_manager.sign_token(Token(user_id))
    response.set_cookie("token", token, httponly=True)


def remove_current_user(response: Response) -> None:
    response.delete_cookie("token")
