from sqlalchemy.orm import Session
from models import test_case as test_case_model
from schemas import test_case as test_case_schema
from typing import List, Optional

def get_test_case(db: Session, test_case_id: int):
    """
    根据ID从数据库中获取单个测试用例
    """
    return db.query(test_case_model.TestCase).filter(test_case_model.TestCase.id == test_case_id).first()

def get_test_cases(db: Session, skip: int = 0, limit: int = 100) -> List[test_case_model.TestCase]:
    """
    从数据库中获取测试用例列表
    """
    return (
        db.query(test_case_model.TestCase)
           .order_by(
            test_case_model.TestCase.priority.asc(), 
            test_case_model.TestCase.created_at.desc()
            )
             .offset(skip)
             .limit(limit)
             .all()
             )


def create_test_case(db: Session, test_case: test_case_schema.TestCaseCreate) -> test_case_model.TestCase:
    """
    在数据库中创建一个新的测试用例
    """
    db_test_case = test_case_model.TestCase(
        name=test_case.name,
        description=test_case.description,
        url=test_case.url,
        method=test_case.method,
        content_type=test_case.content_type,
        headers=test_case.headers,
        body=test_case.body,
        extract_rules=test_case.extract_rules,
        assertions=test_case.assertions
    )
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

def update_test_case(db: Session, test_case_id: int, test_case: test_case_schema.TestCaseUpdate) -> Optional[test_case_model.TestCase]:
    """
    更新数据库中的测试用例
    """
    db_test_case = get_test_case(db, test_case_id)
    if db_test_case:
        update_data = test_case.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_test_case, key, value)
        db.commit()
        db.refresh(db_test_case)
    return db_test_case

def update_test_case_priority(db: Session, test_case_id: int, priority: int) -> Optional[test_case_model.TestCase]:
    """
    更新数据库中测试用例的优先级
    """
    db_test_case = get_test_case(db, test_case_id)
    if db_test_case:
        db_test_case.priority = priority
        db.commit()
        db.refresh(db_test_case)
    return db_test_case