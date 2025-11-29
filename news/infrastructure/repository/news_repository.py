from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from config.database.session import get_db_session
from fastapi import HTTPException
from datetime import datetime
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
                NewsArticleORM.category_id,
                NewsArticleORM.title,
                NewsArticleORM.image_url,
                NewsArticleORM.url,
                NewsArticleORM.published_at,
                NewsArticleORM.summary,
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
                "category_id": r.category_id,
                "title": r.title,
                "category_name": r.category_name,
                "publisher_name": r.publisher_name,
                "image_url": r.image_url,
                "url": r.url,
                "published_at": r.published_at.isoformat(),
                "latest_summary_text": r.summary,
            })

        return {"page": page, "size": size, "total": total, "items": items}

    def get_article_detail(self, db: Session, article_id: int):
        # 1) 기사 본문
        article_stmt = (
            select(
                NewsArticleORM.article_id,
                NewsArticleORM.category_id,
                NewsArticleORM.publisher_id,
                NewsArticleORM.title,
                NewsArticleORM.content,
                NewsArticleORM.summary,
                NewsArticleORM.url,
                NewsArticleORM.image_url,
                NewsArticleORM.published_at,
                NewsArticleORM.crawled_at,
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
        summary_text = summary_row.summary_text if summary_row else article.summary
        summary_created_at = summary_row.created_at if summary_row else article.published_at or article.crawled_at

        return {
            "article_id": article.article_id,
            "category_id": article.category_id,
            "publisher_id": article.publisher_id,
            "title": article.title,
            "content": article.content,
            "category_name": article.category_name,
            "publisher_name": article.publisher_name,
            "url": article.url,
            "image_url": article.image_url,
            "published_at": article.published_at,
            "crawled_at": article.crawled_at,
            "summary_text": summary_text,
            "summary_created_at": summary_created_at,
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

    def list_categories(self, db: Session):
        stmt = select(NewsCategoryORM.category_id, NewsCategoryORM.category_name).order_by(NewsCategoryORM.category_id)
        rows = db.execute(stmt).all()
        return [{"category_id": r.category_id, "category_name": r.category_name} for r in rows]

    def save_article_summary(self, db: Session, article_id: int, summary_text: str):
        article = db.get(NewsArticleORM, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        article.summary = summary_text

        base_date = article.published_at or article.crawled_at or datetime.utcnow()
        record = SummaryHistoryORM(
            article_id=article_id,
            target_type="article",
            target_date=base_date.date(),
            category_id=article.category_id,
            summary_text=summary_text,
            pdf_path=article.pdf_path,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
