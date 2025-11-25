from sqlalchemy.orm import Session

from account.application.port.account_repository_port import AccountRepositoryPort
from account.domain.account import Account
from account.infrastructure.orm.account_orm import AccountORM
from config.database.session import get_db_session


class AccountRepositoryImpl(AccountRepositoryPort):
    __instance__ = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance__ is None:
            cls.__instance__ = super().__new__(cls)
        return cls.__instance__

    def __init__(self):
        if not hasattr(self, 'db'):
            self.db: Session = get_db_session()

    @classmethod
    def getInstance(cls):
        if cls.__instance__ is None:
            cls.__instance__ = cls()
        return cls.__instance__

    def save(self, account: Account) -> Account:
        orm_account = AccountORM(
            email=account.email,
            name=account.name
        )
        self.db.add(orm_account)
        self.db.commit()
        self.db.refresh(orm_account)

        account.id = orm_account.id
        account.created_at = orm_account.created_at
        return account

    def find_by_email(self, email: str) -> Account | None:
        orm_account = self.db.query(AccountORM).filter(AccountORM.email == email).first()
        if orm_account is None:
            return None

        account = Account(
            email=orm_account.email,
            name=orm_account.name
        )
        account.id = orm_account.id
        account.created_at = orm_account.created_at
        return account


