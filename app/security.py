from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Select

from app.db.models import User
from app.db.session import get_session


class JwtService:
    def __init__(self, algorithm, secret, access_token_exp_minutes: int = 15):
        self.algorithm = algorithm
        self.secret = secret
        self.access_token_expiry_minutes = access_token_exp_minutes

    def encode(self, payload: dict[str, str | int]) -> str:
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.access_token_expiry_minutes
        )
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        token = jwt.encode(to_encode, self.secret, self.algorithm)
        return token

    def decode(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired.")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid Token!")


jwt_token_service = JwtService(algorithm="HS256", secret="myprivatesecret")


def get_token_service() -> JwtService:
    return jwt_token_service


def authenticate_user(data, session) -> User | None:
    stmt = Select(User).where(User.username == data.username)
    user = session.execute(stmt).scalar_one_or_none()
    if not user:
        return None
    if not user.verify_password(data.password):
        return None
    return user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/generate_token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    token_service=Depends(get_token_service),
    session=Depends(get_session),
):
    try:
        payload = token_service.decode(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    stmt = Select(User).where(User.username == username)
    user = session.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
