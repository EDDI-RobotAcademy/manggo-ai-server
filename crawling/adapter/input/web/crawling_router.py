from fastapi import APIRouter, HTTPException

from crawling.adapter.input.web.request.crawling_data_request import CrawlingDataRequest
from crawling.adapter.input.web.response.crawling_data_response import CrawlingDataResponse
from crawling.application.usecase.news_crawling_usecase import NewsCrawlingUseCase

crawling_router = APIRouter(tags=["crawling"])
usecase = NewsCrawlingUseCase()


@crawling_router.post("/copy", response_model=CrawlingDataResponse)
async def crawling_data(request: CrawlingDataRequest):
    try:
        result = await usecase.execute(str(request.url), request.category_name)
        return CrawlingDataResponse(
            article_id=result.get("article_id"),
            category_id=result.get("category_id"),
            url=request.url,
            title=result.get("title"),
            contents=result.get("content"),
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
