from pydantic import BaseModel, Field

class WeatherByDateRequest(BaseModel):
    city: str = Field(..., description="City name (e.g., Seoul)")
    date: str = Field(..., description="Target date in YYYY-MM-DD")
