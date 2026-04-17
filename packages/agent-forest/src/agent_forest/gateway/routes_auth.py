"""Auth endpoints: login + /auth/me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from agent_forest.auth import create_access_token
from agent_forest.config import ForestSettings
from agent_forest.gateway.deps import current_user, get_settings, get_user_store
from agent_forest.models import LoginRequest, Token, UserProfile
from agent_forest.users import User, UserStore

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    body: LoginRequest,
    settings: ForestSettings = Depends(get_settings),
    store: UserStore = Depends(get_user_store),
) -> Token:
    user = store.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(user.user_id, settings)
    return Token(access_token=token)


@router.get("/me", response_model=UserProfile)
def me(user: User = Depends(current_user)) -> UserProfile:
    return UserProfile(user_id=user.user_id, username=user.username)
