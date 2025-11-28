from datetime import datetime

from sqlalchemy import BigInteger, Column, Date, DateTime, String, Text

from config.database.session import Base


class SummaryHistoryORM(Base):
    __tablename__ = "SummaryHistory"

    summary_id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    target_type = Column(String(50), nullable=False)
    target_date = Column(Date, nullable=False)
    category_id = Column(BigInteger)
    summary_text = Column(Text, nullable=False)
    pdf_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
