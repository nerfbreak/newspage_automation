"""Auth API routes: login, refresh, me."""
import time
import logging
from fastapi import APIRouter, Depends

from backend.models import LoginRequest, LoginResponse, TokenRefreshRequest, TokenRefreshResponse
from backend.auth import perform_login, perform_refresh
from backend.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    result = perform_login(req.username, req.password)

    if not result["ok"]:
        # 1.5s delay on failed attempts (mirrors app.py brute-force slowdown)
        if not result.get("locked"):
            time.sleep(1.5)
        return LoginResponse(**result)

    return LoginResponse(
        ok=True,
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        expires_in=result["expires_in"],
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(req: TokenRefreshRequest):
    result = perform_refresh(req.refresh_token)
    if not result["ok"]:
        return TokenRefreshResponse(ok=False, error=result["error"])
    return TokenRefreshResponse(
        ok=True,
        access_token=result["access_token"],
        expires_in=result["expires_in"],
    )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"username": user["username"], "status": "authenticated"}
