from abc import ABC, abstractmethod
from typing import List
from report_mail.domain.news import News

class NewsProviderPort(ABC):
    @abstractmethod
    def get_major_news(self) -> List[News]:
        pass
