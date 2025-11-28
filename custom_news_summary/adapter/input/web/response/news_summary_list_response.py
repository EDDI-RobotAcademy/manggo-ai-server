from pydantic import BaseModel
from typing import List

from custom_news_summary.adapter.input.web.response.news_summary_response import NewsSummaryResponse
from custom_news_summary.domain.custom_news import NewsSummary


class NewsSummaryListResponse(BaseModel):
    customNewsList: List[NewsSummaryResponse]
    total: int
    page: int
    size: int

    @classmethod
    def from_news_summary_history(cls, history: list[NewsSummary], page: int, size: int, total: int):

        return cls(
            customNewsList=[NewsSummaryResponse.from_news_summary(n) for n in history],
            total=total,
            page=page,
            size=size
        )