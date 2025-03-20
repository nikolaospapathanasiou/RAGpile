from typing import Annotated, Callable

import jwt
from fastapi import Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from models import User


class TokenManager:
    def __init__(self, secret: str):
        self.secret = secret

    def create_token(self, user_id: str) -> str:
        return jwt.encode({"user_id": user_id}, self.secret, algorithm="HS256")

    def decode_token(self, token: str) -> str:
        return jwt.decode(token, self.secret, algorithms=["HS256"])["user_id"]


def get_current_user_factory(
    token_manager: TokenManager, get_db: Callable[[], Session]
) -> Callable[[Session, str | None], User]:
    def _get_current_user(
        db: Annotated[Session, Depends(get_db)],
        ragpile_token: Annotated[str | None, Cookie(optional=True)] = None,
    ) -> User:
        if not ragpile_token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        user_id = token_manager.decode_token(ragpile_token)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user

    return _get_current_user


def set_current_user(
    response: Response, token_manager: TokenManager, user_id: str
) -> None:
    response.set_cookie("ragpile_token", token_manager.create_token(user_id))


def logout(response: Response) -> None:
    response.delete_cookie("ragpile_token")
