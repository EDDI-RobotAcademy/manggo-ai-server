from pydantic import BaseModel, Field

from news.adapter.input.web.response.news_response import ArticleDetailResponse  # re-export for backward compatibility


class NewsSummaryResponse(BaseModel):
    summary: str = Field(..., description="뉴스 요약 결과")
