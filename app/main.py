from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_session
from app.schema import FormData, UserCreate, UserRead
from app.security import authenticate_user, get_token_service

app = FastAPI()


@app.get("/")
def home():
    return {"hello": "world"}


@app.post("/generate_token")
def get_token(
    data: Annotated[FormData, Form()],
    session=Depends(get_session),
    token_service=Depends(get_token_service),
) -> str | None:
    authenticated_user = authenticate_user(data, session)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Password",
        )
    token = token_service.encode({"sub": authenticated_user.username})
    return token


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate, session: Session = Depends(get_session)
) -> UserRead:
    user = User(**user_in.model_dump())
    session.add(user)
    session.flush()
    return user
