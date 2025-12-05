from sqlalchemy.orm import Session, joinedload
from models import test_report as report_model
from schemas import test_report as report_schema
from typing import List, Optional

def create_test_report(db: Session, report: report_schema.TestReportCreate) -> report_model.TestReport:
    db_report = report_model.TestReport(**report.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_test_report(db: Session, test_report_id: int):
    return db.query(report_model.TestReport).filter(report_model.TestReport.id == test_report_id).options(
        joinedload(report_model.TestReport.records)
    ).first()

def get_test_reports(db: Session, skip: int = 0, limit: int = 100):
    return db.query(report_model.TestReport).order_by(report_model.TestReport.start_time.desc()).offset(skip).limit(limit).all()

def update_test_report(db: Session, report_id: int, report: report_schema.TestReportUpdate) -> Optional[report_model.TestReport]:
    db_report = get_test_report(db, report_id)
    if db_report:
        update_data = report.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_report, key, value)
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
    return db_report

def create_test_record(db: Session, record: report_schema.TestRecordCreate) -> report_model.TestRecord:
    db_record = report_model.TestRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record