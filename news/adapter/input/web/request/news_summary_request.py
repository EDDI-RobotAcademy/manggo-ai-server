from pydantic import BaseModel, Field

class NewsSummarizeRequest(BaseModel):
    text: str = Field(..., description="뉴스 원문 텍스트")
