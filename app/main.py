import os

import uvicorn
import aiohttp
from dotenv import load_dotenv

from login.adapter.input.web.google_oauth_router import login_router
from config.database.session import Base, engine
from login.adapter.input.web.logout_router import logout_router
from custom_news_summary.adapter.input.web.custom_news_summary_router import custom_news_summary_router
from news.adapter.input.web.news_router import news_router
app.include_router(news_router)


load_dotenv()

os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TORCH_USE_CUDA_DSA"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from weather.adapter.input.web.weather_router import weather_router
from crawling.adapter.input.web.crawling_router import crawling_router
from news.adapter.input.web.news_router import news_router

load_dotenv()

app = FastAPI()
load_dotenv()
app.include_router(crawling_router, prefix="/crawling")

origins = [
    "http://localhost:3000",  # Next.js 프론트 엔드 URL
    "http://localhost:2000", # Next.js 프론트 엔드 URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 정확한 origin만 허용
    allow_credentials=True,     # 쿠키 허용
    allow_methods=["*"],        # 모든 HTTP 메서드 허용
    allow_headers=["*"],        # 모든 헤더 허용
)

app.include_router(login_router, prefix="/login")
app.include_router(logout_router, prefix="/logout")
app.include_router(weather_router, prefix="/weather")
app.include_router(news_router, prefix="/news")
app.include_router(custom_news_summary_router, prefix="/custom-news")

from report_mail.infrastructure.scheduler import start_scheduler, job_send_daily_mail
from fastapi import BackgroundTasks

# 앱 실행 시 스케줄러 시작
@app.on_event("startup")
def on_startup():
    start_scheduler()

@app.post("/report-mail/test")
async def test_report_mail(background_tasks: BackgroundTasks):
    """테스트용: 즉시 메일 발송 트리거"""
    background_tasks.add_task(job_send_daily_mail)
    return {"message": "Report mail task triggered in background"}
app.include_router(crawling_router, prefix="/crawling")

# 앱 실행
if __name__ == "__main__":
    host = os.getenv("APP_HOST")
    port = int(os.getenv("APP_PORT"))
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host=host, port=port)
