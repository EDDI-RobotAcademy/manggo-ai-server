import os
from dotenv import load_dotenv

from config.database.session import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from weather.adapter.input.web.weather_router import weather_router

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:2000",  # Next.js 프론트 엔드 URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(weather_router, prefix="/weather")

# 앱 실행
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST")
    port = int(os.getenv("APP_PORT"))
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host=host, port=port)
