from typing import List
from pydantic import BaseModel, Field

class WeatherDataPoint(BaseModel):
    time: str = Field(..., description="Timestamp text from provider")
    temp: float | None = Field(None, description="Temperature in Celsius")
    feels_like: float | None = Field(None, description="Feels-like temperature in Celsius")
    humidity: int | None = Field(None, description="Humidity percentage")
    weather: str | None = Field(None, description="Weather description")
    wind_speed: float | None = Field(None, description="Wind speed")

class WeatherSummaryResponse(BaseModel):
    city: str
    date: str
    data_points: List[WeatherDataPoint]
    summary: str | None = None
