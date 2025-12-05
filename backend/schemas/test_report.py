from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel

class TestRecordBase(BaseModel):
    test_case_id: Optional[int] = None
    case_name: Optional[str] = None
    start_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    request_headers: Optional[Dict[str, Any]] = None
    request_body: Optional[Dict[str, Any]] = None
    response_headers: Optional[Dict[str, Any]] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    assertion_results: Optional[List[Dict[str, Any]]] = None

class TestRecordCreate(TestRecordBase):
    report_id: int

class TestRecordUpdate(TestRecordBase):
    pass

class TestRecord(TestRecordBase):
    id: int
    report_id: int

    class Config:
        from_attributes = True

class TestReportBase(BaseModel):
    suite_id: Optional[int] = None
    suite_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    total_cases: Optional[int] = 0
    pass_count: Optional[int] = 0
    fail_count: Optional[int] = 0
    error_count: Optional[int] = 0
    status: Optional[str] = None

class TestReportCreate(TestReportBase):
    pass

class TestReportUpdate(TestReportBase):
    pass

class TestReport(TestReportBase):
    id: int
    records: List[TestRecord] = []

    class Config:
        from_attributes = True