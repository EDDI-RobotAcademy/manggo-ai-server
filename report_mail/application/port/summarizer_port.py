from abc import ABC, abstractmethod

class SummarizerPort(ABC):
    @abstractmethod
    def summarize(self, text: str) -> str:
        pass
