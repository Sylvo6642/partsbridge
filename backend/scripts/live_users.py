"""Helpers for live tests: create throwaway users, log them in, delete them afterwards."""

import secrets
from contextlib import contextmanager
from uuid import UUID

import httpx

from app.config import settings


def _admin_headers() -> dict:
    key = settings.supabase_service_role_key
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def login(email: str, password: str) -> str:
    response = httpx.post(f"{settings.supabase_url}/auth/v1/token?grant_type=password",
                          headers={"apikey": settings.supabase_anon_key},
                          json={"email": email, "password": password}, timeout=15)
    response.raise_for_status()
    return response.json()["access_token"]


def delete_user(user_id: UUID | str) -> None:
    httpx.delete(f"{settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=_admin_headers(), timeout=15)


@contextmanager
def throwaway_users(client, count: int = 2):
    """Sign up `count` users through the API, yield [(user_id, auth_headers)], then delete them."""
    users = []
    try:
        for _ in range(count):
            email = f"pb-test-{secrets.token_hex(4)}@test.kevinsylvester.xyz"  # never emailed: accounts are created pre-confirmed
            password = secrets.token_urlsafe(12)
            response = client.post("/auth/signup", json={"email": email, "password": password})
            assert response.status_code == 201, response.text
            user_id = response.json()["user_id"]
            users.append((user_id, {"Authorization": f"Bearer {login(email, password)}"}))
        yield users
    finally:
        for user_id, _ in users:
            delete_user(user_id)
