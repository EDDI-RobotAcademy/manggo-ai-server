from sqlalchemy import BigInteger, Column, String

from config.database.session import Base


class NewsCategoryORM(Base):
    __tablename__ = "NewsCategory"

    category_id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    category_name = Column(String(50), nullable=False)
