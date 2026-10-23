"""Sign up and "who am I"."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.auth import User, create_confirmed_user, current_user
from app.db import as_user, connect
from app.seed import seed_workspace

router = APIRouter(tags=["account"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


@router.post("/auth/signup", status_code=201)
def signup(body: SignupRequest):
    """Create a confirmed account and its sandbox workspace. The browser then logs in with Supabase."""
    user_id = create_confirmed_user(body.email, body.password)
    with connect() as conn:
        seed_workspace(conn, user_id, body.email)
    return {"user_id": str(user_id)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    with as_user(user.id) as conn:
        shop = conn.execute("select id, name from sellers where owner_id = %s", (user.id,)).fetchone()
    if not shop:
        raise HTTPException(404, "No workspace for this account")
    return {"user_id": str(user.id), "email": user.email, "shop": {"id": shop[0], "name": shop[1]}}
