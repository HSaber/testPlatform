from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from .test_module import TestModule # 导入 TestModule Schema

class TestCaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: str
    method: str
    content_type: Optional[str] = 'json'
    headers: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    extract_rules: Optional[Dict[str, str]] = None
    assertions: Optional[List[Dict[str, Any]]] = None
    module: Optional[str] = 'default'
    module_id: Optional[int] = None


class TestCaseCreate(TestCaseBase):
    priority: Optional[int] = 0

class TestCaseUpdate(TestCaseBase):
    priority: Optional[int] = 0 # 保持不变

class TestCase(TestCaseBase):
    id: int
    created_at: Any
    updated_at: Optional[Any] = None
    priority: Optional[int] = 0
    
    module_obj: Optional[TestModule] = None # 添加关联对象字段

    class Config:
        from_attributes = True


class TestSuiteExecute(BaseModel):
    test_case_ids: List[int]


class TestCaseBatchDelete(BaseModel):
    test_case_ids: List[int]