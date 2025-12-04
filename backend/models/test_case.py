from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSON # Import JSON type
from sqlalchemy.sql import func

from core.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(String(255), nullable=True)
    url = Column(String(255))
    method = Column(String(10))
    content_type = Column(String(50), default='json')
    headers = Column(JSON, nullable=True)
    body = Column(JSON, nullable=True)
    extract_rules = Column(JSON, nullable=True)
    assertions = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    priority = Column(Integer, index=True, default=0)