from pydantic import BaseModel, HttpUrl, Field

class CrawlingDataRequest(BaseModel):
    url: HttpUrl
    category_name: str = Field(..., description="뉴스 카테고리 이름 (예: Politics, Sports)")
