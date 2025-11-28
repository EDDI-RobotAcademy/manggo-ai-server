from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, Response
from urllib.parse import quote
from sqlalchemy.orm import Session

from app.db import get_db

from news.adapter.input.web.request.news_analyze_request import NewsTextAnalyzeRequest
from news.adapter.input.web.request.news_summary_request import NewsSummarizeRequest
from news.adapter.input.web.response.news_summary_response import NewsSummaryResponse
from news.application.usecase.news_usecase import NewsUseCase, make_pdf_bytes

news_router = APIRouter(tags=["news"])
news_usecase = NewsUseCase()

@news_router.post("/summarize", response_model=NewsSummaryResponse)
async def summarize_news(request: NewsSummarizeRequest):
    result = await news_usecase.summarize_news(request.text)
    # pydantic v1/v2 호환: dict() 사용
    return JSONResponse(content=NewsSummaryResponse(**result).dict())

@news_router.post("/analyze")
async def analyze_news(req: NewsTextAnalyzeRequest):
    return await news_usecase.analyze(
        text=req.text,
        question=req.question,
        max_bullets=req.max_summary_bullets,
        model=req.model,
    )

@news_router.post("/summarize/pdf")
async def summarize_news_pdf(request: NewsSummarizeRequest):
    result = await news_usecase.summarize_news(request.text)
    summary = (result.get("summary") or "").strip()
    if not summary:
        raise HTTPException(status_code=400, detail="summary is empty")

    pdf_bytes = make_pdf_bytes("뉴스 요약", summary)
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=500, detail="PDF generation failed")

    filename = "news_summary.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )

# --- DB: 리스트 뿌리기 / 상세 ---
@news_router.get("/articles")
def list_articles(
    db: Session = Depends(get_db),
    category: str | None = Query(None),
    date: str | None = Query(None, description="YYYY-MM-DD"),
    from_: str | None = Query(None, alias="from", description="YYYY-MM-DD"),
    to: str | None = Query(None, description="YYYY-MM-DD"),
    q: str | None = Query(None, description="title keyword"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    return news_usecase.list_articles(db=db, category=category, date=date, from_=from_, to=to, q=q, page=page, size=size)

@news_router.get("/articles/{article_id}")
def get_article(article_id: int, db: Session = Depends(get_db)):
    return news_usecase.get_article(db=db, article_id=article_id)
