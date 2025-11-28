from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from config.database.session import get_db_session
from news.infrastructure.orm.news_article_orm import NewsArticleORM
from weather.infrastructure.orm.news_category_orm import NewsCategoryORM
from news.infrastructure.orm.publisher_orm import PublisherORM
from weather.infrastructure.orm.summary_history_orm import SummaryHistoryORM

class NewsRepository:
    def list_articles(self, db: Session, page: int, size: int, category_id: int | None = None):
        where = []
        if category_id is not None:
            where.append(NewsArticleORM.category_id == category_id)

        total_stmt = select(func.count()).select_from(NewsArticleORM)
        if where:
            total_stmt = total_stmt.where(*where)
        total = db.execute(total_stmt).scalar_one()

        stmt = (
            select(
                NewsArticleORM.article_id,
                NewsArticleORM.title,
                NewsArticleORM.image_url,
                NewsArticleORM.url,
                NewsArticleORM.published_at,
                NewsCategoryORM.category_name,
                PublisherORM.publisher_name,
            )
            .select_from(NewsArticleORM)
            .join(NewsCategoryORM, NewsCategoryORM.category_id == NewsArticleORM.category_id)
            .outerjoin(PublisherORM, PublisherORM.publisher_id == NewsArticleORM.publisher_id)
            .order_by(desc(NewsArticleORM.published_at))
            .offset((page - 1) * size)
            .limit(size)
        )
        if where:
            stmt = stmt.where(*where)

        rows = db.execute(stmt).all()

        items = []
        for r in rows:
            items.append({
                "article_id": r.article_id,
                "title": r.title,
                "category_name": r.category_name,
                "publisher_name": r.publisher_name,
                "image_url": r.image_url,
                "url": r.url,
                "published_at": r.published_at.isoformat(),
            })

        return {"page": page, "size": size, "total": total, "items": items}

    def get_article_detail(self, db: Session, article_id: int):
        # 1) 기사 본문
        article_stmt = (
            select(
                NewsArticleORM.article_id,
                NewsArticleORM.title,
                NewsArticleORM.content,
                NewsArticleORM.url,
                NewsArticleORM.image_url,
                NewsArticleORM.published_at,
                NewsCategoryORM.category_name,
                PublisherORM.publisher_name,
            )
            .select_from(NewsArticleORM)
            .join(NewsCategoryORM, NewsCategoryORM.category_id == NewsArticleORM.category_id)
            .outerjoin(PublisherORM, PublisherORM.publisher_id == NewsArticleORM.publisher_id)
            .where(NewsArticleORM.article_id == article_id)
        )
        article = db.execute(article_stmt).first()
        if not article:
            return None

        # 2) 같은 article_id의 최신 요약(SummaryHistory)
        summary_stmt = (
            select(SummaryHistoryORM.summary_text, SummaryHistoryORM.created_at)
            .where(SummaryHistoryORM.article_id == article_id)
            .order_by(desc(SummaryHistoryORM.created_at))
            .limit(1)
        )
        summary_row = db.execute(summary_stmt).first()

        return {
            "article_id": article.article_id,
            "title": article.title,
            "content": article.content,
            "category_name": article.category_name,
            "publisher_name": article.publisher_name,
            "url": article.url,
            "image_url": article.image_url,
            "published_at": article.published_at.isoformat(),
            "summary_text": summary_row.summary_text if summary_row else None,
            "summary_created_at": summary_row.created_at.isoformat() if summary_row else None,
        }

    def get_latest_summary(self, db: Session, article_id: int):
        summary_stmt = (
            select(
                SummaryHistoryORM.summary_id,
                SummaryHistoryORM.summary_text,
                SummaryHistoryORM.created_at,
            )
            .where(SummaryHistoryORM.article_id == article_id)
            .order_by(desc(SummaryHistoryORM.created_at))
            .limit(1)
        )
        summary = db.execute(summary_stmt).first()
        if not summary:
            return None
        return {
            "summary_id": summary.summary_id,
            "article_id": article_id,
            "summary_text": summary.summary_text,
            "created_at": summary.created_at.isoformat() if summary.created_at else None,
        }
