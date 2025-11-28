from pydantic import BaseModel


class CustomNewsHistoryDetailRequest(BaseModel):
    summary_id: int