from abc import ABC, abstractmethod


class TextSummarizerPort(ABC):
    """Summarizer Port - 인터페이스"""

    @abstractmethod
    def summarize(self, content: str) -> tuple[str, str]:
        """Returns (title, summary_text)"""
        pass