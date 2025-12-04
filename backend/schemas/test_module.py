from pydantic import BaseModel
from typing import Optional, List

class TestModuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class TestModuleCreate(TestModuleBase):
    pass

class TestModuleUpdate(TestModuleBase):
    pass

class TestModule(TestModuleBase):
    id: int
    children: List['TestModule'] = []

    class Config:
        from_attributes = True