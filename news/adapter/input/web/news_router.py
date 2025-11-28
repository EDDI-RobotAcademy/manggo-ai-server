from fastapi import APIRouter
from fastapi.responses import JSONResponse

from news.adapter.input.web.request.news_analyze_request import NewsTextAnalyzeRequest
from news.adapter.input.web.request.news_summary_request import NewsSummarizeRequest
from news.adapter.input.web.response.news_summary_response import NewsSummaryResponse
from news.application.usecase.news_usecase import NewsUseCase

news_router = APIRouter(tags=["news"])
news_usecase = NewsUseCase()

@news_router.post("/summarize", response_model=NewsSummaryResponse)
async def summarize_news(request: NewsSummarizeRequest):
    result = await news_usecase.summarize_news(request.text)
    return JSONResponse(content=NewsSummaryResponse(**result).dict())

@news_router.post("/analyze")
async def analyze_news(req: NewsTextAnalyzeRequest):
    if not (req.text or "").strip():
        raise HTTPException(status_code=400, detail="Empty text")

    cleaned = clean_news_text(req.text)
    if not cleaned:
        raise HTTPException(status_code=400, detail="No usable text after cleaning")

    chunks = chunk_text(cleaned)
    if not chunks:
        raise HTTPException(status_code=500, detail="Chunking failed")

    summary = await summarize_news_chunks(model=req.model, chunks=chunks, max_bullets=req.max_summary_bullets)

    answer = None
    if req.question and req.question.strip():
        answer = await qa_on_summary(model=req.model, summary=summary, question=req.question.strip())

    analysis = await analyze_opinions(model=req.model, summary=summary)

    return {
        "cleaned_text": cleaned,
        "chunk_count": len(chunks),
        "summary": summary,
        "answer": answer,
        "analysis": analysis,
    }