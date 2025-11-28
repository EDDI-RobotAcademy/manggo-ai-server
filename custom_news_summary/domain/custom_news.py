from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class SourceType(Enum):
    URL = "URL"
    PDF = "PDF"


@dataclass
class NewsSummary:
    """뉴스 요약 도메인 엔티티"""
    summary_id: Optional[int]
    user_id: str
    source_type: SourceType
    source_url: Optional[str]
    file_name: Optional[str]
    file_path: Optional[str]
    summary_title: str
    summary_text: str
    created_at: Optional[datetime] = None

    @classmethod
    def from_orm(cls, orm) -> 'NewsSummary':
        """ORM 객체를 도메인 객체로 변환"""
        return cls(
            summary_id=orm.summary_id,
            user_id=orm.user_id,
            source_type=orm.source_type,
            source_url=orm.source_url,
            file_name=orm.file_name,
            file_path=orm.file_path,
            summary_title=orm.summary_title,
            summary_text=orm.summary_text,
            created_at=orm.created_at
        )
