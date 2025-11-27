from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from config.database.session import get_db_session
from weather.infrastructure.orm.news_category_orm import NewsCategoryORM
from weather.infrastructure.orm.summary_history_orm import SummaryHistoryORM
from weather.infrastructure.orm.weather_data_orm import WeatherDataORM


class WeatherRepository:
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

    def save_weather_data(
        self,
        target_date: date,
        temperature: Optional[float],
        humidity: Optional[int],
        wind_speed: Optional[float],
        description: Optional[str],
        raw_json,
    ) -> WeatherDataORM:
        record = WeatherDataORM(
            date=target_date,
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            description=description,
            raw_json=raw_json,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def save_summary(
        self,
        target_type: str,
        target_date: date,
        summary_text: str,
        category_id: Optional[int] = None,
        pdf_path: Optional[str] = None,
    ) -> SummaryHistoryORM:
        record = SummaryHistoryORM(
            target_type=target_type,
            target_date=target_date,
            category_id=category_id,
            summary_text=summary_text,
            pdf_path=pdf_path,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_latest_summary(
        self,
        target_type: str,
        target_date: date,
        category_id: Optional[int] = None,
    ) -> Optional[SummaryHistoryORM]:
        query = self.db.query(SummaryHistoryORM).filter(
            SummaryHistoryORM.target_type == target_type,
            SummaryHistoryORM.target_date == target_date,
        )
        if category_id is not None:
            query = query.filter(SummaryHistoryORM.category_id == category_id)
        return query.order_by(SummaryHistoryORM.created_at.desc()).first()

    def get_latest_weather_data(self, target_date: date) -> Optional[WeatherDataORM]:
        return (
            self.db.query(WeatherDataORM)
            .filter(WeatherDataORM.date == target_date)
            .order_by(WeatherDataORM.created_at.desc())
            .first()
        )

    def get_category_id_by_name(self, name: str) -> Optional[int]:
        category = (
            self.db.query(NewsCategoryORM)
            .filter(NewsCategoryORM.category_name == name)
            .first()
        )
        return category.category_id if category else None
