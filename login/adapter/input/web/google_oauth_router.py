import os
import uuid

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from account.application.usecase.create_or_get_account_usecase import CreateOrGetAccountUsecase
from config.redis.redis_config import get_redis
from login.application.usecase.google_oauth_usecase import GoogleOAuthUsecase
from login.infrastructure.service.google_oauth_service import GoogleOAuthService

login_router = APIRouter()
googleOAuthService = GoogleOAuthService()
google_usecase = GoogleOAuthUsecase.getInstance(googleOAuthService)
account_usecase = CreateOrGetAccountUsecase.getInstance()

redis_client = get_redis()

@login_router.get("/google")
async def redirect_to_google():
    url = google_usecase.get_authorization_url()
    return RedirectResponse(url)

@login_router.get("/google/redirect")
async def process_google_redirect(
        code: str,
        state: str | None = None
):

    result = google_usecase.fetch_user_profile(code, state or "")
    profile = result["profile"]
    access_token = result["access_token"]
    print("profile:", profile)

    # 계정 생성/조회
    account = account_usecase.create_or_get_account(
        profile.get("email"),
        profile.get("name")
    )

    # 세션 id 생성
    session_id = str(uuid.uuid4())

    redis_client.hset(
        session_id,
        mapping= {
            "email": profile.get("email"),
            "access_token": access_token.access_token
        }
    )
    redis_client.expire(session_id, 3600)

    print("[INFO] Session saved in Redis: ", redis_client.exists(session_id))

    # 브라우저 쿠키 발급
    redirect_response = RedirectResponse(os.getenv("WEB_URI"))
    redirect_response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600
    )
    return redirect_response
