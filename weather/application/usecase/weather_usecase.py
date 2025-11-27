import os
from datetime import datetime
from typing import List, Optional, Tuple

import httpx
from fastapi import HTTPException
from openai import OpenAI

from weather.adapter.input.web.response.weather_summary_response import WeatherDataPoint
from weather.infrastructure.repository.weather_repository import WeatherRepository

DEFAULT_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
WEATHER_CATEGORY_NAME = "Weather"


class WeatherUseCase:
    def __init__(
        self,
        api_key: Optional[str] = None,
        forecast_url: Optional[str] = None,
        openai_client: Optional[OpenAI] = None,
        repository: Optional[WeatherRepository] = None,
    ):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.forecast_url = forecast_url or os.getenv("OPENWEATHER_FORECAST_URL") or DEFAULT_FORECAST_URL
        self.openai_client = openai_client
        self.repository = repository or WeatherRepository.getInstance()
        self.summary_category_id: Optional[int] = None

    async def fetch_weather_by_date(self, city: str, date_str: str) -> dict:
        target_date = self._parse_date(date_str)
        if not self.api_key:
            raise HTTPException(status_code=500, detail="OPENWEATHER_API_KEY is not configured.")

        target_type = self._target_type(city)
        category_id = self._get_summary_category_id()

        cached_summary = self.repository.get_latest_summary(
            target_type=target_type,
            target_date=target_date,
            category_id=category_id,
        )
        if cached_summary:
            cached_weather = self.repository.get_latest_weather_data(target_date)
            raw_points = cached_weather.raw_json if cached_weather and cached_weather.raw_json else []
            data_points = self._raw_to_data_points(raw_points)
            return {
                "city": city,
                "date": date_str,
                "data_points": data_points,
                "summary": cached_summary.summary_text,
            }

        forecast = await self._get_forecast(city)
        matched_points = self._filter_by_date(forecast, target_date)
        if not matched_points:
            raise HTTPException(status_code=404, detail="No data for that date (OpenWeatherMap provides ~5 days).")

        cleaned = [self._clean_point(m) for m in matched_points]
        summary = await self._summarize(city, date_str, cleaned)

        try:
            self._persist(target_type, target_date, cleaned, summary, category_id)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Failed to store weather summary.") from exc

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

    def _raw_to_data_points(self, raw_points: List[dict]) -> List[WeatherDataPoint]:
        data_points: List[WeatherDataPoint] = []
        for item in raw_points:
            try:
                data_points.append(WeatherDataPoint(**item))
            except Exception:
                continue
        return data_points

    def _persist(
        self,
        target_type: str,
        target_date,
        data_points: List[WeatherDataPoint],
        summary: Optional[str],
        category_id: int,
    ):
        avg_temp, avg_humidity, avg_wind = self._aggregate_metrics(data_points)
        description = data_points[0].weather if data_points else None
        raw_json = [p.dict() for p in data_points]

        self.repository.save_weather_data(
            target_date=target_date,
            temperature=avg_temp,
            humidity=avg_humidity,
            wind_speed=avg_wind,
            description=description,
            raw_json=raw_json,
        )

        if summary:
            self.repository.save_summary(
                target_type=target_type,
                target_date=target_date,
                summary_text=summary,
                category_id=category_id,
            )

    def _aggregate_metrics(self, data_points: List[WeatherDataPoint]) -> Tuple[Optional[float], Optional[int], Optional[float]]:
        if not data_points:
            return None, None, None

        temps = [p.temp for p in data_points if p.temp is not None]
        hums = [p.humidity for p in data_points if p.humidity is not None]
        winds = [p.wind_speed for p in data_points if p.wind_speed is not None]

        def _avg(values):
            return sum(values) / len(values) if values else None

        avg_temp = _avg(temps)
        avg_hum = int(_avg(hums)) if hums else None
        avg_wind = _avg(winds)
        return avg_temp, avg_hum, avg_wind

    async def _summarize(self, city: str, date_str: str, data_points: List[WeatherDataPoint]) -> Optional[str]:
        client = self._get_openai_client()
        if client is None:
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

    async def get_summary_tts(self, city: str, date_str: str) -> bytes:
        result = await self.fetch_weather_by_date(city, date_str)
        summary_text = result.get("summary")
        if not summary_text:
            raise HTTPException(status_code=404, detail="Summary not available for that date.")

        client = self._get_openai_client()
        if client is None:
            raise HTTPException(status_code=500, detail="OpenAI client not configured.")

        model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        voice = os.getenv("OPENAI_TTS_VOICE", "alloy")

        try:
            with client.audio.speech.with_streaming_response.create(
                model=model,
                voice=voice,
                input=summary_text,
            ) as response:
                audio_bytes = b"".join(response.iter_bytes())
        except Exception as exc:
            raise HTTPException(status_code=502, detail="TTS generation failed.") from exc

        return audio_bytes

    def _get_openai_client(self) -> Optional[OpenAI]:
        if self.openai_client:
            return self.openai_client
        try:
            self.openai_client = OpenAI()
        except Exception:
            self.openai_client = None
        return self.openai_client

    def _target_type(self, city: str) -> str:
        normalized = city.strip().lower()
        return f"weather:{normalized}"

    def _get_summary_category_id(self) -> int:
        if self.summary_category_id is not None:
            return self.summary_category_id

        category_id = self.repository.get_category_id_by_name(WEATHER_CATEGORY_NAME)
        if category_id is None:
            raise HTTPException(status_code=500, detail="Weather category not found in NewsCategory.")

        self.summary_category_id = category_id
        return category_id
