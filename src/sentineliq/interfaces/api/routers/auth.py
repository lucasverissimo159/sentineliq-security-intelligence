"""Authentication and authorization endpoints for the SentinelIQ API.

Uses a very small JWT strategy that is appropriate for the current
portfolio scope. This keeps the API contract documented and testable
without adding a database-backed user table during the first iteration.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from sentineliq.infrastructure.security.jwt_auth import (
    create_access_token,
    decode_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="admin")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 60
    scopes: list[str]


class UserIdentity(BaseModel):
    username: str
    scopes: list[str]


async def _current_user(authorization: Annotated[str | None, Header(alias="Authorization")] = None) -> UserIdentity:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    username = payload.get("sub")
    scopes = payload.get("scopes") or []
    if not isinstance(username, str) or not isinstance(scopes, list):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return UserIdentity(username=username, scopes=[str(item) for item in scopes])


@router.post("/token", response_model=TokenResponse)
async def issue_token(payload: TokenRequest) -> TokenResponse:
    """Issue a JWT bearer token for demo portfolio authentication.

    Username/password is intentionally demo-friendly and mapped to a
    single accepted admin user so the project remains easy to run locally.
    """
    if payload.username == "admin" and payload.password == "admin":
        scopes = ["logs:write", "logs:read", "alerts:read", "reports:write"]
        token = create_access_token(payload.username, scopes=scopes)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=60,
            scopes=scopes,
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.get("/me", response_model=UserIdentity)
async def whoami(user: UserIdentity = Depends(_current_user)) -> UserIdentity:
    """Return the identity associated with the bearer token."""
    return user
