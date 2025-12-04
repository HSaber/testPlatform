from typing import List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session, joinedload
from models.test_suite import TestSuite, TestSuiteItem
from schemas.test_suite import TestSuiteCreate, TestSuiteUpdate, TestSuiteItemCreate

def get_test_suite(db: Session, test_suite_id: int):
    return db.query(TestSuite).options(
        joinedload(TestSuite.items).joinedload(TestSuiteItem.test_case),
        joinedload(TestSuite.items).joinedload(TestSuiteItem.module),
        joinedload(TestSuite.items).joinedload(TestSuiteItem.child_suite)
    ).filter(TestSuite.id == test_suite_id).first()

def get_test_suites(db: Session, skip: int = 0, limit: int = 100):
    return db.query(TestSuite).options(
        joinedload(TestSuite.items).joinedload(TestSuiteItem.test_case),
        joinedload(TestSuite.items).joinedload(TestSuiteItem.module),
        joinedload(TestSuite.items).joinedload(TestSuiteItem.child_suite)
    ).offset(skip).limit(limit).all()

def _create_item(db: Session, suite_id: int, item_in: Union[TestSuiteItemCreate, Dict[str, Any]]):
    if isinstance(item_in, dict):
        db_item = TestSuiteItem(
            suite_id=suite_id,
            item_type=item_in.get("item_type"),
            test_case_id=item_in.get("test_case_id"),
            module_id=item_in.get("module_id"),
            child_suite_id=item_in.get("child_suite_id"),
            sort_order=item_in.get("sort_order", 0)
        )
    else:
        db_item = TestSuiteItem(
            suite_id=suite_id,
            item_type=item_in.item_type,
            test_case_id=item_in.test_case_id,
            module_id=item_in.module_id,
            child_suite_id=item_in.child_suite_id,
            sort_order=item_in.sort_order
        )
    db.add(db_item)

def create_test_suite(db: Session, test_suite: TestSuiteCreate):
    # 提取 items 数据
    items_data = test_suite.items if hasattr(test_suite, 'items') and test_suite.items else []
    
    # 创建 TestSuite 实例（排除 items）
    db_test_suite = TestSuite(
        name=test_suite.name,
        description=test_suite.description,
        parent_id=test_suite.parent_id
    )
    db.add(db_test_suite)
    db.flush()  # 获取 ID

    # 创建 TestSuiteItem 记录
    for item_in in items_data:
        _create_item(db, db_test_suite.id, item_in)

    db.commit()
    db.refresh(db_test_suite)
    return db_test_suite

def update_test_suite(db: Session, test_suite_id: int, test_suite: TestSuiteUpdate):
    db_test_suite = get_test_suite(db, test_suite_id)
    if not db_test_suite:
        return None
        
    update_data = test_suite.dict(exclude_unset=True)
    
    # 处理 items 更新
    if "items" in update_data:
        items_data = update_data.pop("items")
        
        # 使用 ORM 方式清空旧 items，这样 Session 状态会自动同步
        # 因为在 models 中配置了 cascade="all, delete-orphan"，
        # 从 items 集合中移除对象会自动触发删除操作
        db_test_suite.items = []
        
        # 添加新的 items
        for item_in in items_data:
            # 构造新的 TestSuiteItem 对象
            if isinstance(item_in, dict):
                new_item = TestSuiteItem(
                    item_type=item_in.get("item_type"),
                    test_case_id=item_in.get("test_case_id"),
                    module_id=item_in.get("module_id"),
                    child_suite_id=item_in.get("child_suite_id"),
                    sort_order=item_in.get("sort_order", 0)
                )
            else:
                new_item = TestSuiteItem(
                    item_type=item_in.item_type,
                    test_case_id=item_in.test_case_id,
                    module_id=item_in.module_id,
                    child_suite_id=item_in.child_suite_id,
                    sort_order=item_in.sort_order
                )
            # 添加到集合中，Session 会自动处理
            db_test_suite.items.append(new_item)

    # 更新其他字段
    for key, value in update_data.items():
        setattr(db_test_suite, key, value)

    db.add(db_test_suite)
    db.commit()
    db.refresh(db_test_suite)
    return db_test_suite

def delete_test_suite(db: Session, test_suite_id: int):
    db_test_suite = get_test_suite(db, test_suite_id)
    if db_test_suite:
        # 先删除引用此套件作为子套件的 TestSuiteItem 记录，防止外键约束错误
        db.query(TestSuiteItem).filter(TestSuiteItem.child_suite_id == test_suite_id).delete()
        
        # 删除套件本身（SQLAlchemy 的 cascade 会自动处理属于此套件的 items）
        db.delete(db_test_suite)
        db.commit()
    return db_test_suite