# news/adapter/input/web/response/article_response.py
from pydantic import BaseModel, Field
from typing import List, Optional

class ArticleListItem(BaseModel):
    id: int
    title: str
    source: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    published_at: str  # ISO string

class ArticleListResponse(BaseModel):
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1, le=100)
    total: int
    items: List[ArticleListItem]

class ArticleDetailResponse(BaseModel):
    id: int
    title: str
    source: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    published_at: str
    content: str
