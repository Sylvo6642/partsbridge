"""Who is calling? Verify the Supabase login token (JWT) on every request.

The browser logs in with Supabase and sends `Authorization: Bearer <token>`. We check the token's signature
against Supabase's public keys (JWKS), so nobody can fake a user id. The user id then comes from the token,
never from the request body, and never from the AI.
"""

from dataclasses import dataclass
from functools import cache
from uuid import UUID

import httpx
import jwt
from fastapi import Header, HTTPException

from app.config import settings


@dataclass(frozen=True)
class User:
    id: UUID
    email: str


@cache
def _jwks() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json", cache_keys=True)


def current_user(authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Log in first")
    token = authorization.removeprefix("Bearer ")
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=["ES256", "RS256"], audience="authenticated")
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Invalid or expired login: {e}") from e
    return User(id=UUID(claims["sub"]), email=claims.get("email", ""))


def create_confirmed_user(email: str, password: str) -> UUID:
    """Create an account through Supabase's admin API, already confirmed (no confirmation email needed)."""
    response = httpx.post(
        f"{settings.supabase_url}/auth/v1/admin/users",
        headers={"apikey": settings.supabase_service_role_key,
                 "Authorization": f"Bearer {settings.supabase_service_role_key}"},
        json={"email": email, "password": password, "email_confirm": True},
        timeout=15,
    )
    if response.status_code >= 400:
        message = response.json().get("msg") or response.json().get("message") or response.text
        raise HTTPException(400 if response.status_code < 500 else 502, message)
    return UUID(response.json()["id"])
