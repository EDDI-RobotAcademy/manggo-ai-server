from typing import List
from pydantic import BaseModel, field_validator, HttpUrl


class CrawlingDataResponse(BaseModel):
    url: HttpUrl
    title:str
    contents:str

    @field_validator("contents")
    def limit_contents_length(cls, v: str) -> str:
        max_len = 500  # 원하는 길이
        if v is None:
            return v
        if len(v) > max_len:
            return v[:max_len] + "..."  # 잘렸다는 표시
        return v