from typing import Tuple, List

from sqlalchemy import String

from custom_news_summary.application.port.crawler_port import ContentCrawlerPort
from custom_news_summary.application.port.storage_port import FileStoragePort
from custom_news_summary.application.port.summarizer_port import TextSummarizerPort
from custom_news_summary.domain.custom_news import NewsSummary, SourceType
from custom_news_summary.infrastructure.repository.custom_new_repository_impl import CustomNewsSummaryRepositoryImpl


class CreateNewsSummaryUseCase:
    def __init__(
            self,
            repository: CustomNewsSummaryRepositoryImpl,
            crawler: ContentCrawlerPort,
            summarizer: TextSummarizerPort,
            file_storage: FileStoragePort
    ):
        self.repository = repository
        self.crawler = crawler
        self.summarizer = summarizer
        self.file_storage = file_storage

    def execute_from_url(self, user_id: str, url: str) -> NewsSummary:
        content = self.crawler.crawl(url)

        print("[INFO] content", content)
        if not content:
            raise ValueError("크롤링이 불가능한 url입니다.")

        # title, summary_text = self.summarizer.summarize(content)

        # 3. 도메인 엔티티 생성
        news_summary = NewsSummary(
            summary_id=None,
            user_id=user_id,
            source_type=SourceType.URL,
            source_url=url,
            file_name=None,
            file_path=None,
            summary_title=content[:10],
            summary_text=content
            # summary_title=title,
            # summary_text=summary_text
        )

        # 4. 저장
        return self.repository.save(news_summary)

    def execute_from_pdf(self, user_id: str, file_content: bytes, file_name: str) -> NewsSummary:
        file_path = self.file_storage.save_file(file_content, file_name)

        content = "PDF에서 추출한 텍스트"

        title, summary_text = self.summarizer.summarize(content)

        # 4. 도메인 엔티티 생성
        news_summary = NewsSummary(
            summary_id=None,
            user_id=user_id,
            source_type=SourceType.PDF,
            source_url=None,
            file_name=file_name,
            file_path=file_path,
            summary_title=title,
            summary_text=summary_text
        )

        # 5. 저장
        return self.repository.save(news_summary)


    def get_all_custom_news_history(self, user_id: str, page: int = 1, size: int = 10) -> Tuple[List[NewsSummary], int]:
        custom_news_history, total = self.repository.find_all(user_id, page, size)
        return custom_news_history, total

    def get_custom_new_history_detail(self, summary_id: int, user_id: str) -> NewsSummary:
        summary = self.repository.get_custom_new_history_detail(summary_id, user_id)
        return summary
