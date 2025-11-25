from abc import ABC, abstractmethod

from account.domain.account import Account


class AccountRepositoryPort(ABC):

    @abstractmethod
    def save(self, account: Account):
        pass

    @abstractmethod
    def find_by_email(self, email: str):
        pass
