from datetime import datetime

from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, JSON, Numeric, String

from config.database.session import Base


class WeatherDataORM(Base):
    __tablename__ = "WeatherData"

    weather_id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    date = Column(Date, nullable=False)
    temperature = Column(Numeric(5, 2))
    humidity = Column(Integer)
    wind_speed = Column(Numeric(5, 2))
    description = Column(String(255))
    raw_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
