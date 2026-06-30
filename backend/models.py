from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from backend.database import Base


class Client(Base):
    """Sales meeting record from CSV."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    meeting_date = Column(DateTime, nullable=True)
    vendor = Column(String(100), nullable=True)
    closed = Column(Boolean, default=False)
    transcription = Column(Text, nullable=True)
    sector = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)
    inquiry_volume = Column(String(50), nullable=True)
    channel = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    integrations = Column(String(255), nullable=True)
    tone = Column(String(100), nullable=True)
    usage_type = Column(String(100), nullable=True)
    pain = Column(String(100), nullable=True)
    concreteness = Column(String(50), nullable=True)
    categorized = Column(Boolean, default=False)
