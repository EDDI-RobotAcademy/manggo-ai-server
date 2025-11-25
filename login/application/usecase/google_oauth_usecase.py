from login.adapter.input.web.request.get_access_token_request import GetAccessTokenRequest
from login.infrastructure.service.google_oauth_service import GoogleOAuthService


class GoogleOAuthUsecase:
    _instance = None

    def __new__(cls, service: GoogleOAuthService):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.service = service
        return cls._instance

    @classmethod
    def getInstance(cls, service: GoogleOAuthService | None = None):
        if cls._instance is None:
            if service is None:
                raise ValueError("GoogleOAuthService must be provided for first initialization")
            cls(service)
        elif service is not None and getattr(cls._instance, "service", None) is None:
            cls._instance.service = service
        return cls._instance

    def get_authorization_url(self) -> str:
        return self.service.get_authorization_url()

    def fetch_user_profile(self, code: str, state: str) -> dict:
        token_request = GetAccessTokenRequest(state=state, code=code)
        access_token = self.service.refresh_access_token(token_request)

        profile = self.service.fetch_user_profile(access_token)
        return {"profile": profile, "access_token": access_token}


