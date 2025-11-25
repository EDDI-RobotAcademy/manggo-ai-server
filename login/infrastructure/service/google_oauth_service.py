import os
from urllib.parse import quote

import requests

from login.adapter.input.web.request.get_access_token_request import GetAccessTokenRequest
from login.adapter.input.web.response.access_token import AccessToken

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

class GoogleOAuthService:

    # 인증 URL 생성
    def get_authorization_url(self) -> str:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        redirect_uri = quote(os.getenv("GOOGLE_REDIRECT_URI"), safe='')
        scope = "openid email profile"
        return (
            f"{GOOGLE_AUTH_URL}"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope={quote(scope)}"
        )

    # Access token 생성
    def refresh_access_token(self, request: GetAccessTokenRequest) -> AccessToken:
        data = {
            "code" : request.code,
            "client_id" : os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret" : os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri" : os.getenv("GOOGLE_REDIRECT_URI"),
            "grant_type" : "authorization_code"
        }
        response = requests.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        token_data = response.json()

        return AccessToken(
            access_token=token_data.get("access_token"),
            token_type=token_data.get("token_type"),
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token")
        )

    # Access token을 통한 사용자 생성
    def fetch_user_profile(self, access_token: AccessToken):
        headers = {"Authorization" : f"Bearer {access_token.access_token}"}
        response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
        response.raise_for_status()
        return response.json()
