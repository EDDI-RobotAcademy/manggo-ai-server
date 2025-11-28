from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, String
from config.database.session import Base

class PublisherORM(Base):
    __tablename__ = "Publisher"

    publisher_id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    publisher_name = Column(String(100), nullable=False)
    logo_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
