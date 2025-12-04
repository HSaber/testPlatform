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

def reorder_test_cases(db: Session, test_case_ids: List[int]) -> List[test_case_model.TestCase]:
    """根据提供的ID列表重新排序测试用例"""
    updated_test_cases = []
    for index, test_case_id in enumerate(test_case_ids):
        db_test_case = db.query(test_case_model.TestCase).filter(test_case_model.TestCase.id == test_case_id).first()
        if db_test_case:
            db_test_case.priority = index  # 使用索引作为新的优先级
            updated_test_cases.append(db_test_case)
    db.bulk_save_objects(updated_test_cases)
    db.commit()
    # 刷新以获取更新后的对象状态
    for tc in updated_test_cases:
        db.refresh(tc)
    return updated_test_cases

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

def delete_test_case(db: Session, test_case_id: int) -> Optional[test_case_model.TestCase]:
    """
    从数据库中删除一个测试用例
    """
    db_test_case = get_test_case(db, test_case_id)
    if db_test_case:
        db.delete(db_test_case)
        db.commit()
    return db_test_case

def delete_test_cases(db: Session, test_case_ids: List[int]) -> int:
    """
    批量删除测试用例
    """
    # 使用 in_ 操作符进行批量查询和删除
    # synchronize_session=False 用于提高性能，因为我们不打算立即使用这些对象
    result = db.query(test_case_model.TestCase).filter(test_case_model.TestCase.id.in_(test_case_ids)).delete(synchronize_session=False)
    db.commit()
    return result


def copy_test_case(db: Session, test_case_id: int):
    # 获取源用例
    db_test_case = get_test_case(db, test_case_id)
    if not db_test_case:
        return None
    
    # 创建新用例数据，排除id、created_at和updated_at
    exclude_columns = {"id", "created_at", "updated_at"}
    new_data = {
        column.name: getattr(db_test_case, column.name)
        for column in test_case_model.TestCase.__table__.columns
        if column.name not in exclude_columns
    }
    
    # 修改名称以示区分
    new_data["name"] = f"{new_data['name']}_Copy"
    
    # 创建新实例
    new_test_case = test_case_model.TestCase(**new_data)
    db.add(new_test_case)
    db.commit()
    db.refresh(new_test_case)
    return new_test_case