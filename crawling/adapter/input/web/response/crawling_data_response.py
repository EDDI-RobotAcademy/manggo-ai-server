from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CrawlingDataResponse(BaseModel):
    article_id: Optional[int] = Field(None, description="Saved NewsArticle ID")
    category_id: Optional[int] = Field(None, description="Resolved category id")
    url: HttpUrl
    title: str
    contents: str

    @field_validator("contents")
    def limit_contents_length(cls, v: str) -> str:
        max_len = 500  # 응답 본문 길이 제한
        if v is None:
            return v
        if len(v) > max_len:
            return v[:max_len] + "..."  # 잘린 표시
        return v
