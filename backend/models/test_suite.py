from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from core.database import Base

# 定义关联项的类型枚举
class SuiteItemType(str, enum.Enum):
    test_case = "test_case"
    test_module = "test_module"
    test_suite = "test_suite"

class TestSuiteItem(Base):
    __tablename__ = "test_suite_items"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    
    # 关联项类型
    item_type = Column(Enum(SuiteItemType), nullable=False)
    
    # 关联项ID（为了更好的数据完整性，这里我们使用分别的外键，尽管会稍微冗余一些）
    # 在逻辑层确保这三个字段有且仅有一个有值
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=True)
    module_id = Column(Integer, ForeignKey("test_modules.id"), nullable=True)
    child_suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=True)
    
    # 排序字段
    sort_order = Column(Integer, default=0)

    # 关系定义
    suite = relationship("TestSuite", foreign_keys=[suite_id], back_populates="items")
    test_case = relationship("TestCase")
    module = relationship("TestModule")
    child_suite = relationship("TestSuite", foreign_keys=[child_suite_id])

class TestSuite(Base):
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(String(255), nullable=True)
    
    # 所属父级套件（虽然 TestSuiteItem 也能表达层级，但保留 parent_id 作为基础归属关系可能仍有意义，
    # 或者我们可以完全依赖 TestSuiteItem 来构建树。为了简化，这里暂时保留 parent_id 作为简单的归类，
    # 但实际的执行顺序和包含关系主要由 items 决定。）
    parent_id = Column(Integer, ForeignKey("test_suites.id"), nullable=True)
    children = relationship("TestSuite", backref="parent", remote_side=[id], foreign_keys=[parent_id])

    # 统一的一对多关系
    items = relationship("TestSuiteItem", back_populates="suite", cascade="all, delete-orphan", order_by="TestSuiteItem.sort_order", foreign_keys=[TestSuiteItem.suite_id])

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())