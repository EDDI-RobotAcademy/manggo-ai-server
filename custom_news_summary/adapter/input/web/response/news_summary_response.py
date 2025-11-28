from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from custom_news_summary.domain.custom_news import NewsSummary


class NewsSummaryResponse(BaseModel):
    """응답 DTO"""
    summary_id: int
    user_id: str
    source_type: str
    source_url: Optional[str]
    file_name: Optional[str]
    summary_title: str
    summary_text: str
    created_at: datetime

    @classmethod
    def from_news_summary(cls, summary: NewsSummary):
        return cls(
            summary_id=summary.summary_id,
            user_id=summary.user_id,
            source_type=summary.source_type.value,
            source_url=summary.source_url,
            file_name=summary.file_name,
            summary_title=summary.summary_title,
            summary_text=summary.summary_text,
            created_at=summary.created_at
        )