from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy import JSON  # Fix: Use generic JSON for MySQL compatibility
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base

class TestReport(Base):
    __tablename__ = "test_reports"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=True) # 可以为空，支持单用例执行
    suite_name = Column(String(100)) # 冗余存储，防止套件删除后无法显示
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    duration = Column(Float) # 总耗时(秒)
    total_cases = Column(Integer, default=0)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    status = Column(String(20)) # running, completed, error

    records = relationship("TestRecord", back_populates="report", cascade="all, delete-orphan")

class TestRecord(Base):
    __tablename__ = "test_records"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("test_reports.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=True)
    case_name = Column(String(100))
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    duration = Column(Float)
    status = Column(String(20)) # pass, fail, error
    
    url = Column(String(500))
    method = Column(String(10))
    status_code = Column(Integer)
    request_headers = Column(JSON)
    request_body = Column(JSON)
    response_headers = Column(JSON)
    response_body = Column(Text) # 响应体可能很大，用Text
    error_message = Column(Text)
    
    # 断言结果详情，存储为JSON列表
    # e.g. [{check: "status_code", expect: 200, actual: 200, result: true}]
    assertion_results = Column(JSON) 

    report = relationship("TestReport", back_populates="records")