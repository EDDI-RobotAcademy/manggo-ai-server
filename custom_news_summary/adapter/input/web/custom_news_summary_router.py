import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Cookie, Query

from config.redis.redis_config import get_redis
from custom_news_summary.adapter.input.web.request.news_summary_request import CreateNewsSummaryURLRequest
from custom_news_summary.adapter.input.web.response.news_summary_list_response import NewsSummaryListResponse
from custom_news_summary.adapter.input.web.response.news_summary_response import NewsSummaryResponse
from custom_news_summary.application.usecase.custom_news_summary_usecase import CreateNewsSummaryUseCase
from custom_news_summary.infrastructure.external.beautifulsoup_crawler import BeautifulSoupCrawler
from custom_news_summary.infrastructure.external.local_file_storage import LocalFileStorage
from custom_news_summary.infrastructure.external.openai_summarizer import OpenAISummarizer
from custom_news_summary.infrastructure.repository.custom_new_repository_impl import CustomNewsSummaryRepositoryImpl

custom_news_summary_router = APIRouter(tags=["custom_news_summary"])

redis_client = get_redis()
custom_news_summary_usecase = CreateNewsSummaryUseCase(
    repository=CustomNewsSummaryRepositoryImpl(),
    crawler=BeautifulSoupCrawler(),                 
    summarizer=OpenAISummarizer(),
    file_storage=LocalFileStorage()                 
)

@custom_news_summary_router.get("/list", response_model=NewsSummaryListResponse)
async def get_custom_news_history_list(
    session_id: str | None = Cookie(None),
page: int = Query(1, ge=1), size: int = Query(10, ge=1)
):
    try:

        print("sessionId :" , session_id )
        data = redis_client.hgetall(session_id)

        if not data:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        user_id = data.get("email")

        historys, total = custom_news_summary_usecase.get_all_custom_news_history(user_id, page, size)

        print("[INFO] history ", historys)
        return NewsSummaryListResponse.from_news_summary_history(historys, page, size, total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@custom_news_summary_router.post("/url", response_model=NewsSummaryResponse)
async def create_summary_from_url(
        request: CreateNewsSummaryURLRequest,
        session_id: str | None = Cookie(None)
):
    """URL로부터 뉴스 요약 생성"""
    try:
        data = redis_client.hgetall(session_id)

        if not data:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        user_id = data.get("email")

        print(request.url)
        summary = custom_news_summary_usecase.execute_from_url(user_id, str(request.url))

        return NewsSummaryResponse(
            summary_id=summary.summary_id,
            user_id=summary.user_id,
            source_type=summary.source_type.value,
            source_url=summary.source_url,
            file_name=summary.file_name,
            summary_title=summary.summary_title,
            summary_text=summary.summary_text,
            created_at=summary.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_news_summary_router.post("/pdf", response_model=NewsSummaryResponse)
async def create_summary_from_pdf(
        file: UploadFile = File(...),
        session_id: str | None = Cookie(None)
):
    """PDF 파일로부터 뉴스 요약 생성"""
    try:

        data = redis_client.hgetall(session_id)

        if not data:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        user_id = data.get("email")

        # 파일 검증
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다")

        # 파일 읽기
        file_content = await file.read()

        summary = custom_news_summary_usecase.execute_from_pdf(user_id, file_content, file.filename)

        return NewsSummaryResponse(
            summary_id=summary.summary_id,
            user_id=summary.user_id,
            source_type=summary.source_type.value,
            source_url=summary.source_url,
            file_name=summary.file_name,
            summary_title=summary.summary_title,
            summary_text=summary.summary_text,
            created_at=summary.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))