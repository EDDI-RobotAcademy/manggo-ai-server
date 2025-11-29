from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from config.database.session import get_db_session
from news.infrastructure.orm.news_article_orm import NewsArticleORM
from weather.infrastructure.orm.news_category_orm import NewsCategoryORM


class NewsArticleRepository:
    """Repository for NewsArticle with minimal helpers to resolve category."""

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        if not hasattr(self, "db"):
            self.db: Session = get_db_session()

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def get_category_id_by_name(self, category_name: str) -> Optional[int]:
        category = (
            self.db.query(NewsCategoryORM)
            .filter(NewsCategoryORM.category_name == category_name)
            .first()
        )
        return category.category_id if category else None

    def save_article(
        self,
        *,
        category_id: int,
        title: str,
        content: str,
        url: Optional[str] = None,
        summary: Optional[str] = None,
        publisher_id: Optional[int] = None,
        image_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ) -> NewsArticleORM:
        record = NewsArticleORM(
            category_id=category_id,
            publisher_id=publisher_id,
            title=title,
            content=content,
            summary=summary,
            url=url,
            image_url=image_url,
            published_at=published_at or datetime.utcnow(),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
