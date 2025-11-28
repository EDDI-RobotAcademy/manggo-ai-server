from pydantic import BaseModel, Field

class NewsSummaryResponse(BaseModel):
    summary: str = Field(..., description="뉴스 요약 결과")
