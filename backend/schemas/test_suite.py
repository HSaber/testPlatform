from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel
from schemas.test_case import TestCase
from schemas.test_module import TestModule

# 定义 TestSuiteItem 的 Pydantic 模型
class TestSuiteItemCreate(BaseModel):
    item_type: Literal['test_case', 'test_module', 'test_suite']
    test_case_id: Optional[int] = None
    module_id: Optional[int] = None
    child_suite_id: Optional[int] = None
    sort_order: int = 0

class TestSuiteItem(BaseModel):
    id: int
    suite_id: int
    item_type: str
    test_case_id: Optional[int] = None
    module_id: Optional[int] = None
    child_suite_id: Optional[int] = None
    sort_order: int
    
    # 关联对象信息
    test_case: Optional[TestCase] = None
    module: Optional[TestModule] = None
    # 注意：为了避免循环引用，这里暂时不包含 child_suite 的完整详情，或者只包含基本信息

    class Config:
        orm_mode = True

class TestSuiteBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class TestSuiteCreate(TestSuiteBase):
    items: List[TestSuiteItemCreate] = []

class TestSuiteUpdate(TestSuiteBase):
    items: Optional[List[TestSuiteItemCreate]] = None

class TestSuite(TestSuiteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    items: List[TestSuiteItem] = []

    class Config:
        orm_mode = True

class TestSuiteDebugRequest(BaseModel):
    suite_id: int
    include_case_ids: Optional[List[int]] = None

# 新增：用于 URL 路径末尾包含 suite_id 时的请求体
class TestSuiteDebugBody(BaseModel):
    include_case_ids: Optional[List[int]] = None

class TestSuiteDebugResponse(BaseModel):
    suite_id: int
    suite_name: str
    results: List[dict]
    total_duration: float