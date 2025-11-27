from fastapi import APIRouter
from fastapi.responses import JSONResponse

from news.adapter.input.web.request.news_summary_request import NewsSummarizeRequest
from news.adapter.input.web.response.news_summary_response import NewsSummaryResponse
from news.application.usecase.news_usecase import NewsUseCase

news_router = APIRouter(tags=["news"])
news_usecase = NewsUseCase()

@news_router.post("/summarize", response_model=NewsSummaryResponse)
async def summarize_news(request: NewsSummarizeRequest):
    result = await news_usecase.summarize_news(request.text)
    return JSONResponse(content=NewsSummaryResponse(**result).dict())
