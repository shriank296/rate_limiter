from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_session
from app.schema import UserCreate, UserRead

app = FastAPI()


@app.get("/")
def home():
    return {"hello": "world"}


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate, session: Session = Depends(get_session)
) -> UserRead:
    user = User(**user_in.model_dump())
    session.add(user)
    session.flush()
    return user
