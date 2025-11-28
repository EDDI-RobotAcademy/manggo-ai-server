from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text
from config.database.session import Base

class NewsArticleORM(Base):
    __tablename__ = "NewsArticle"

    article_id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    category_id = Column(BigInteger, ForeignKey("NewsCategory.category_id"), nullable=False)
    publisher_id = Column(BigInteger, ForeignKey("Publisher.publisher_id"))

    title = Column(String(500), nullable=False)
    content = Column(Text)        # MEDIUMTEXT도 Text로 OK
    summary = Column(Text)        # NewsArticle.summary 컬럼도 존재

    url = Column(String(500))
    image_url = Column(String(500))
    published_at = Column(DateTime, nullable=False)
    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    pdf_path = Column(String(500))
