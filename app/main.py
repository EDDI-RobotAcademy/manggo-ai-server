import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from config.database.session import Base, engine
from crawling.adapter.input.web.crawling_router import crawling_router
from custom_news_summary.adapter.input.web.custom_news_summary_router import custom_news_summary_router
from login.adapter.input.web.google_oauth_router import login_router
from login.adapter.input.web.logout_router import logout_router
from news.adapter.input.web.news_router import news_router
from report_mail.infrastructure.scheduler import start_scheduler, job_send_daily_mail
from weather.adapter.input.web.weather_router import weather_router


load_dotenv()

# CUDA 디버깅 옵션
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TORCH_USE_CUDA_DSA"] = "1"

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:2000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(login_router, prefix="/login")
app.include_router(logout_router, prefix="/logout")
app.include_router(weather_router, prefix="/weather")
app.include_router(news_router, prefix="/news")
app.include_router(custom_news_summary_router, prefix="/custom-news")
app.include_router(crawling_router, prefix="/crawling")


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.post("/report-mail/test")
async def test_report_mail(background_tasks: BackgroundTasks):
    """테스트용: 즉시 메일 전송 트리거"""
    background_tasks.add_task(job_send_daily_mail)
    return {"message": "Report mail task triggered in background"}


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "33333"))
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host=host, port=port)
