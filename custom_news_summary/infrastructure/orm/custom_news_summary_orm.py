from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
import enum

from config.database.session import Base

class SourceType(enum.Enum):
    URL = "URL"
    PDF = "PDF"

class CustomNewsSummaryORM(Base):
    __tablename__ = "CustomNewsSummary"

    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    source_url = Column(String(1000))
    file_name = Column(String(255))
    file_path = Column(String(255))
    summary_title = Column(String(100))
    summary_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())