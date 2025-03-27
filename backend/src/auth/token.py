import datetime
from calendar import timegm
from typing import Annotated, Callable

import jwt
from fastapi import Cookie, Depends, HTTPException, Response
from jwt.exceptions import PyJWTError
from sqlalchemy.orm import Session

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

    @classmethod
    def from_payload(cls, payload: dict) -> "Self":
        return cls(payload["user_id"], payload["exp"])


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
        return Token(**jwt.decode(token, self.secret, algorithms=["HS256"]))


def get_current_user_factory(
    token_manager: TokenManager, get_db: Callable[[], Session]
) -> Callable[[Session, str | None], User]:
    def _get_current_user(
        response: Response,
        db: Annotated[Session, Depends(get_db)],
        ragpile_token: Annotated[str | None, Cookie(optional=True)] = None,
    ) -> User:
        if not ragpile_token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            token = token_manager.decode_token(ragpile_token)
        except PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Not authenticated") from exc

        if token.expires_soon():
            set_current_user(response, token_manager, token.user_id)

        user = db.query(User).filter(User.id == token.user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user

    return _get_current_user


def set_current_user(
    response: Response, token_manager: TokenManager, user_id: str
) -> None:
    token = token_manager.sign_token(Token(user_id))
    response.set_cookie("ragpile_token", token, httponly=True)


def remove_current_user(response: Response) -> None:
    response.delete_cookie("ragpile_token")
