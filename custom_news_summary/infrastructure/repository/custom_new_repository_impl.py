from sqlalchemy import String

from config.database.session import get_db_session
from sqlalchemy.orm import Session

from custom_news_summary.application.port.custom_new_repository_port import CustomNewsSummaryRepositoryPort
from custom_news_summary.domain.custom_news import NewsSummary
from custom_news_summary.infrastructure.orm.custom_news_summary_orm import CustomNewsSummaryORM, SourceType


class CustomNewsSummaryRepositoryImpl(CustomNewsSummaryRepositoryPort):
    def __init__(self):
        self.db: Session = get_db_session()

    def save(self, news_summary: NewsSummary) -> NewsSummary:
        """도메인 → ORM 변환 후 저장"""

        # 1. 도메인 엔티티 → ORM 엔티티 변환
        orm_entity = self._to_orm(news_summary)

        # 2. DB 저장
        self.db.add(orm_entity)
        self.db.commit()
        self.db.refresh(orm_entity)

        # 3. ORM → 도메인 엔티티 변환 후 반환
        return self._to_domain(orm_entity)

    def find_by_user_id(self, user_id: str) -> list[NewsSummary]:

        # 1. ORM으로 조회
        orm_results = self.session.query(CustomNewsSummaryORM) \
            .filter_by(user_id=user_id) \
            .all()

        # 2. ORM → 도메인 엔티티 변환
        return [self._to_domain(orm) for orm in orm_results]

    def _to_orm(self, domain: NewsSummary) -> CustomNewsSummaryORM:
        """도메인 → ORM 변환"""
        return CustomNewsSummaryORM(
            user_id=domain.user_id,
            source_type=SourceType[domain.source_type.name],
            source_url=domain.source_url,
            file_name=domain.file_name,
            file_path=domain.file_path,
            summary_title=domain.summary_title,
            summary_text=domain.summary_text
        )

    def _to_domain(self, orm: CustomNewsSummaryORM) -> NewsSummary:
        """ORM → 도메인 변환"""
        return NewsSummary(
            summary_id=orm.summary_id,
            user_id=orm.user_id,
            source_type=SourceType[orm.source_type.name],
            source_url=orm.source_url,
            file_name=orm.file_name,
            file_path=orm.file_path,
            summary_title=orm.summary_title,
            summary_text=orm.summary_text,
            created_at=orm.created_at
        )

    def find_all(self, user_id: str, page: int, size: int) -> tuple[list[NewsSummary], int]:
        query = self.db.query(CustomNewsSummaryORM).filter(CustomNewsSummaryORM.user_id == user_id)

        total = query.count()

        print(total)
        orms = query.offset((page - 1) * size).limit(size).all()
        print(orms)
        return [NewsSummary.from_orm(orm) for orm in orms], total