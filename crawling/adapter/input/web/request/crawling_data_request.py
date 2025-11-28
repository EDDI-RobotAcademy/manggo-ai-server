from pydantic import BaseModel, HttpUrl

class CrawlingDataRequest(BaseModel):
    url: HttpUrl