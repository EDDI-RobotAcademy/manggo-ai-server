from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ArticleListItemResponse(BaseModel):
    article_id: int
    title: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    published_at: datetime
    crawled_at: datetime

    category_id: int
    category_name: Optional[str] = None

    publisher_id: Optional[int] = None
    publisher_name: Optional[str] = None
    publisher_logo_url: Optional[str] = None

    latest_summary_text: Optional[str] = None


class ArticleListResponse(BaseModel):
    page: int
    size: int
    total: int
    items: List[ArticleListItemResponse]


class ArticleDetailResponse(BaseModel):
    article_id: int
    category_id: int
    publisher_id: Optional[int] = None

    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    published_at: datetime
    crawled_at: datetime
    pdf_path: Optional[str] = None

    category_name: Optional[str] = None
    publisher_name: Optional[str] = None
    publisher_logo_url: Optional[str] = None

    # 최신 요약 정보
    summary_text: Optional[str] = None
    summary_created_at: Optional[datetime] = None


class ArticleSummaryResponse(BaseModel):
    summary_id: int
    article_id: int
    target_type: str
    summary_text: str
    created_at: datetime
