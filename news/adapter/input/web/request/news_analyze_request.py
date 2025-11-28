from pydantic import BaseModel, Field
from typing import Optional

class NewsTextAnalyzeRequest(BaseModel):
    text: str = Field(..., description="뉴스 원문 텍스트")
    question: Optional[str] = Field(None, description="요약 기반으로 답할 질문(선택)")
    max_summary_bullets: int = Field(6, ge=3, le=12, description="요약 불릿 개수(3~12)")
    model: str = Field("gpt-4.1", description="사용 모델명")
