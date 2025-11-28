from datetime import datetime
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, String, Text
from config.database.session import Base

class SummaryHistoryORM(Base):
    __tablename__ = "SummaryHistory"

    summary_id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    article_id = Column(BigInteger, ForeignKey("NewsArticle.article_id"))
    target_type = Column(String(50), nullable=False)
    target_date = Column(Date, nullable=False)
    category_id = Column(BigInteger, ForeignKey("NewsCategory.category_id"))

    summary_text = Column(Text, nullable=False)  # MEDIUMTEXT
    pdf_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
