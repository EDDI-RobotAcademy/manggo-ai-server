from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, BigInteger, Index

class Base(DeclarativeBase):
    pass

class Article(Base):
    __tablename__ = "news_article"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str | None] = mapped_column(String(128))
    category: Mapped[str | None] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(String(1024))
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_article_published_at", "published_at"),
        Index("ix_article_category_published_at", "category", "published_at"),
    )
