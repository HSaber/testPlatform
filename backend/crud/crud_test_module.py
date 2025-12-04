from sqlalchemy.orm import Session
from models.test_module import TestModule
from schemas.test_module import TestModuleCreate, TestModuleUpdate

def get_test_module(db: Session, module_id: int):
    return db.query(TestModule).filter(TestModule.id == module_id).first()

def get_test_modules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(TestModule).offset(skip).limit(limit).all()

def create_test_module(db: Session, module: TestModuleCreate):
    db_module = TestModule(**module.model_dump())
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

def update_test_module(db: Session, module_id: int, module: TestModuleUpdate):
    db_module = get_test_module(db, module_id)
    if not db_module:
        return None
    update_data = module.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_module, key, value)
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

def delete_test_module(db: Session, module_id: int):
    db_module = get_test_module(db, module_id)
    if db_module:
        db.delete(db_module)
        db.commit()
    return db_module