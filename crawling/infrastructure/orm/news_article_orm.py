from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)

from config.database.session import Base


class NewsArticleORM(Base):
    __tablename__ = "NewsArticle"

    article_id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    category_id = Column(BigInteger, nullable=False)
    publisher_id = Column(BigInteger, nullable=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String(500))
    image_url = Column(String(500))
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    pdf_path = Column(String(500))
