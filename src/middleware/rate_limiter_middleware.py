import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.config import config
from fastapi import status, HTTPException
from typing import Dict
from fastapi.responses import JSONResponse
import uuid

request_counters: Dict[str, int] = {}
last_request_times: Dict[str, float] = {}


async def create_session_id(response: JSONResponse) -> str:
    """Generate and set a new session ID."""
    session_id = str(uuid.uuid4())
    response.set_cookie(key="session_id", value=session_id, secure=True, httponly=True)
    return session_id


class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore
        session_id = request.cookies.get("session_id")

        if not session_id:
            response = JSONResponse(content={"message": "New session created."})
            session_id = await create_session_id(response)
            response.headers["X-New-Session-ID"] = session_id
        current_time = time.time()

        if (
            session_id not in last_request_times
            or current_time - last_request_times[session_id] > config.RATE_LIMIT_WINDOW
        ):
            request_counters[session_id] = 0
            last_request_times[session_id] = current_time

        request_counters[session_id] += 1

        if request_counters[session_id] > config.MAX_REQUESTS_PER_WINDOW:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )

        response = await call_next(request)
        return response
