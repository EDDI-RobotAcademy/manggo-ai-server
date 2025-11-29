from pydantic import BaseModel, Field
from typing import Optional

class NewsSummarizeRequest(BaseModel):
    text: str = Field(..., description="뉴스 원문 텍스트")
    article_id: Optional[int] = Field(None, description="요약을 저장할 기사 ID (선택)")
