from fastapi import APIRouter
from fastapi.responses import JSONResponse

from weather.adapter.input.web.request.weather_by_date_request import WeatherByDateRequest
from weather.adapter.input.web.response.weather_summary_response import WeatherSummaryResponse
from weather.application.usecase.weather_usecase import WeatherUseCase

weather_router = APIRouter(tags=["weather"])
weather_usecase = WeatherUseCase()

@weather_router.post("/by-date", response_model=WeatherSummaryResponse)
async def weather_by_date(request: WeatherByDateRequest):
    result = await weather_usecase.fetch_weather_by_date(request.city, request.date)
    return JSONResponse(content=WeatherSummaryResponse(**result).dict())
