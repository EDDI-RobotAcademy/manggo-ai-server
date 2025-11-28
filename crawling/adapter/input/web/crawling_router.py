from http.client import HTTPException
import asyncio
import requests

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel,HttpUrl

from crawling.adapter.input.web.request.crawling_data_request import CrawlingDataRequest
from crawling.adapter.input.web.response.crawling_data_response import CrawlingDataResponse
import asyncio
from crawling.domain.service.web_crawling import run_crawling
crawling_router = APIRouter(tags=["crawling"])

@crawling_router.post("/copy", response_model=CrawlingDataResponse)
async def crawling_data(request: CrawlingDataRequest):
    try:
        # run_crawling이 str을 기대하면 str(url)로 캐스팅
        url = str(request.url)
        title, text = await asyncio.wait_for(run_crawling(str(url)), timeout=300)

        if not title:
            raise HTTPException(status_code=400, detail="title is empty.")
        if not text:
            raise HTTPException(status_code=400, detail="contents is empty.")

        return CrawlingDataResponse(
            url=url,
            title=title,
            contents=text
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="요청 처리 시간이 5분을 초과했습니다.")
    except HTTPException as e:
        print(title)
        print(text)
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))