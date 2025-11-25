from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from config.database.session import Base

class AccountORM(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), unique=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

