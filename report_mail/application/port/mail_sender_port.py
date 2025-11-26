from abc import ABC, abstractmethod

class MailSenderPort(ABC):
    @abstractmethod
    def send_mail(self, to: str, subject: str, content: str) -> None:
        pass
