from datetime import datetime

from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, String, Text

from config.database.session import Base


class SummaryHistoryORM(Base):
    __tablename__ = "SummaryHistory"

    summary_id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    # 뉴스 기사 연동 시 사용할 수 있도록 optional FK 추가
    article_id = Column(BigInteger, ForeignKey("NewsArticle.article_id"), nullable=True, index=True)
    target_type = Column(String(50), nullable=False)
    target_date = Column(Date, nullable=False)
    category_id = Column(BigInteger)
    summary_text = Column(Text, nullable=False)
    pdf_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
