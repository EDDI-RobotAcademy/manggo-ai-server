import os
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import HTTPException
from openai import OpenAI

from weather.adapter.input.web.response.weather_summary_response import WeatherDataPoint

DEFAULT_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

class WeatherUseCase:
    def __init__(self, api_key: Optional[str] = None, forecast_url: Optional[str] = None, openai_client: Optional[OpenAI] = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.forecast_url = forecast_url or os.getenv("OPENWEATHER_FORECAST_URL") or DEFAULT_FORECAST_URL
        self.openai_client = openai_client

    async def fetch_weather_by_date(self, city: str, date_str: str) -> dict:
        target_date = self._parse_date(date_str)
        if not self.api_key:
            raise HTTPException(status_code=500, detail="OPENWEATHER_API_KEY is not configured.")

        forecast = await self._get_forecast(city)
        matched_points = self._filter_by_date(forecast, target_date)
        if not matched_points:
            raise HTTPException(status_code=404, detail="No data for that date (OpenWeatherMap provides ~5 days).")

        cleaned = [self._clean_point(m) for m in matched_points]
        summary = await self._summarize(city, date_str, cleaned)

        return {
            "city": city,
            "date": date_str,
            "data_points": cleaned,
            "summary": summary,
        }

    def _parse_date(self, date_str: str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD required)")

    async def _get_forecast(self, city: str) -> dict:
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "lang": "kr",
        }

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(self.forecast_url, params=params)

        if res.status_code == 401:
            raise HTTPException(status_code=502, detail="Weather provider rejected the API key.")
        if res.status_code == 404:
            raise HTTPException(status_code=404, detail="Invalid city name or not found.")
        if res.status_code >= 400:
            raise HTTPException(status_code=502, detail="Weather provider error.")

        return res.json()

    def _filter_by_date(self, forecast: dict, target_date) -> List[dict]:
        matched = []
        for item in forecast.get("list", []):
            dt_txt = item.get("dt_txt")
            if not dt_txt:
                continue
            try:
                item_date = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                continue
            if item_date == target_date:
                matched.append(item)
        return matched

    def _clean_point(self, item: dict) -> WeatherDataPoint:
        return WeatherDataPoint(
            time=item.get("dt_txt"),
            temp=item.get("main", {}).get("temp"),
            feels_like=item.get("main", {}).get("feels_like"),
            humidity=item.get("main", {}).get("humidity"),
            weather=((item.get("weather") or [{}])[0].get("description")),
            wind_speed=item.get("wind", {}).get("speed"),
        )

    async def _summarize(self, city: str, date_str: str, data_points: List[WeatherDataPoint]) -> Optional[str]:
        client = self.openai_client
        if client is None:
            try:
                client = OpenAI()
            except Exception:
                return None

        prompt = f"""
다음은 {date_str} {city}의 시간대별 예보입니다.
사용자에게 도움이 되도록 핵심만 간결하게 정리해줘:
- 전체 요약 1~2줄 (체감 온도 포함)
- 시간대별 주요 변화(기온/체감/습도/날씨/바람) 한 줄씩
- 외출/우산/보온/바람 대비 등 간단 팁 1~2개

데이터(JSON):
{[p.dict() for p in data_points]}
"""
        try:
            ai_response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception:
            return None

        choice = ai_response.choices[0].message
        if isinstance(choice, dict):
            return choice.get("content")
        return getattr(choice, "content", None)
