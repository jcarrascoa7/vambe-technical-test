from sqlalchemy import Column, Integer

from backend.database import Base


class Client(Base):
    """Placeholder model — fields added in feature 2 (ETL pipeline)."""

    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
