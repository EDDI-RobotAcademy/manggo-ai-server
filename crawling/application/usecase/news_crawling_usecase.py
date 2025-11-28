import asyncio
from datetime import datetime
from typing import Optional, Tuple

from fastapi import HTTPException

from crawling.domain.service.web_crawling import run_crawling
from crawling.infrastructure.repository.news_article_repository import NewsArticleRepository


class NewsCrawlingUseCase:
    """Handle crawling flow: validate, crawl, map category, persist."""

    def __init__(self, repository: Optional[NewsArticleRepository] = None):
        self.repository = repository or NewsArticleRepository.getInstance()

    async def execute(self, url: str, category_name: str) -> dict:
        category_name = (category_name or "").strip()
        if not category_name:
            raise HTTPException(status_code=400, detail="category_name is required.")

        category_id = self.repository.get_category_id_by_name(category_name)
        if category_id is None:
            raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found.")

        title, content = await self._crawl(url)
        if not title:
            raise HTTPException(status_code=400, detail="Crawled title is empty.")
        if not content:
            raise HTTPException(status_code=400, detail="Crawled content is empty.")

        article = self.repository.save_article(
            category_id=category_id,
            title=title,
            content=content,
            url=url,
            published_at=datetime.utcnow(),
        )

        return {
            "article_id": article.article_id,
            "category_id": category_id,
            "title": title,
            "content": content,
            "url": url,
        }

    async def _crawl(self, url: str) -> Tuple[str, str]:
        if not url:
            raise HTTPException(status_code=400, detail="url is required.")
        try:
            # enforce timeout to avoid hanging crawls
            return await asyncio.wait_for(run_crawling(url), timeout=300)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
