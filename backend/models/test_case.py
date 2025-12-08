from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum, DateTime
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
import enum


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

    # 新增脚本字段
    setup_script = Column(String(5000), nullable=True)     # 前置脚本
    teardown_script = Column(String(5000), nullable=True)  # 后置脚本

    module = Column(String(100), index=True, default='default') # 暂时保留，后续迁移数据后可删除
    module_id = Column(Integer, ForeignKey("test_modules.id"), nullable=True)
    
    module_obj = relationship("TestModule", back_populates="test_cases")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    priority = Column(Integer, index=True, default=0) # 确保 priority 字段保留