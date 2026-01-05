from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import Select

from app.db.models import User


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
