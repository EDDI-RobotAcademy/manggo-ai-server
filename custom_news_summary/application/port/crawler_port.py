from abc import ABC, abstractmethod


class ContentCrawlerPort(ABC):

    @abstractmethod
    def crawl(self, url: str) -> str:
        pass