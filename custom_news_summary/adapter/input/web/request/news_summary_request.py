from pydantic import BaseModel, HttpUrl


class CreateNewsSummaryURLRequest(BaseModel):
    url: HttpUrl