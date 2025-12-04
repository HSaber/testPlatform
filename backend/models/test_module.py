from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class TestModule(Base):
    __tablename__ = "test_modules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    description = Column(String(255), nullable=True)
    parent_id = Column(Integer, ForeignKey("test_modules.id"), nullable=True)
    
    # 建立自关联关系，remote_side=[id] 表示 id 是远程侧（即父节点）
    parent = relationship("TestModule", remote_side=[id], backref="children")
    
    # 关联用例，cascade="all, delete" 表示删除模块时级联处理（可选，视需求而定，这里暂不级联删除用例，避免误删）
    test_cases = relationship("TestCase", back_populates="module_obj")