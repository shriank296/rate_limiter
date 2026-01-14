import datetime
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request, status
from redis import Redis

from app.db.models import User
from app.security import get_current_user

rate_limit_store = defaultdict(deque)
ALLOWED_REQUESTS_PER_USER = 1
WINDOW_SECONDS = 60


def rate_limit_guard(user: User = Depends(get_current_user)) -> None:
    now = int(datetime.datetime.now().timestamp())
    window_start = now - WINDOW_SECONDS

    if user.username not in rate_limit_store:
        rate_limit_store[user.username] = deque()

    timestamps = rate_limit_store[user.username]

    # Remove old timestamps
    while timestamps and timestamps[0] < window_start:
        timestamps.popleft()

    # Check limit
    if len(timestamps) >= ALLOWED_REQUESTS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later",
        )

    # Record current request
    timestamps.append(now)


def get_redis_client() -> Redis:
    from app.redis import redis_client

    return redis_client


def check_rate_limit(
    redis_client: Redis,
    key: str,
    limit: int = ALLOWED_REQUESTS_PER_USER,
    window: int = WINDOW_SECONDS,
):
    count = redis_client.incr(key)

    if count == 1:
        redis_client.expire(key, window)

    if count > limit:
        retry_after = redis_client.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
            headers={"Retry-After": str(retry_after)},
        )


def rate_limit_guard_using_redis(
    request: Request,
    user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis_client),
) -> None:
    key = f"rate_limiting:user:{user.id}:endpoint:{request.url.path}"
    check_rate_limit(redis, key)
