from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import String

from custom_news_summary.domain.custom_news import NewsSummary


class CustomNewsSummaryRepositoryPort(ABC):

    @abstractmethod
    def save(self, news_summary: NewsSummary) -> NewsSummary:
        pass

    @abstractmethod
    def find_all(self, user_id: String, page: int, size: int) -> list[NewsSummary]:
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> list[NewsSummary]:
        pass
