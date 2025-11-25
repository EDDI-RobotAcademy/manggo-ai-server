from huggingface_hub import repo_info

from account.domain.account import Account
from account.infrastructure.repository.account_repository_impl import AccountRepositoryImpl


class CreateOrGetAccountUsecase:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.repo = AccountRepositoryImpl.getInstance()
        return cls.__instance

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def create_or_get_account(self, email: str, name: str | None):
        account = self.repo.find_by_email(email)
        if account:
            return account

        if not name:
            name = "noname"

        account = Account(email=email, name=name)
        return self.repo.save(account)


