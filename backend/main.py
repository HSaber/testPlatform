from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from core.database import SessionLocal, engine, Base
from models import test_case as test_case_model
from crud import crud_test_case
from schemas import test_case as test_case_schema
from services.test_runner import TestRunner
from typing import List
from pydantic import BaseModel

test_case_model.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS 中间件配置
origins = [
    "http://localhost:5173",  # 允许的前端地址
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许访问的源
    allow_credentials=True,  # 支持 cookie
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有标头
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/testcases/", response_model=test_case_schema.TestCase)
def create_test_case(test_case: test_case_schema.TestCaseCreate, db: Session = Depends(get_db)):
    """
    创建一个新的测试用例
    """
    return crud_test_case.create_test_case(db=db, test_case=test_case)

@app.put("/testcases/{test_case_id}", response_model=test_case_schema.TestCase)
def update_test_case(test_case_id: int, test_case: test_case_schema.TestCaseUpdate, db: Session = Depends(get_db)):
    """
    更新一个测试用例
    """
    db_test_case = crud_test_case.update_test_case(db=db, test_case_id=test_case_id, test_case=test_case)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return db_test_case

@app.delete("/testcases/{test_case_id}", response_model=test_case_schema.TestCase)
def delete_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """
    删除一个测试用例
    """
    db_test_case = crud_test_case.delete_test_case(db=db, test_case_id=test_case_id)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return db_test_case

@app.post("/testcases/batch_delete")
def batch_delete_test_cases(batch_delete: test_case_schema.TestCaseBatchDelete, db: Session = Depends(get_db)):
    """
    批量删除测试用例
    """
    deleted_count = crud_test_case.delete_test_cases(db=db, test_case_ids=batch_delete.test_case_ids)
    return {"message": "Test cases deleted successfully", "deleted_count": deleted_count}

@app.get("/testcases/list", response_model=List[test_case_schema.TestCase])
def read_test_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    test_cases = crud_test_case.get_test_cases(db, skip=skip, limit=limit)
    return test_cases

@app.post("/testsuites/execute")
def execute_test_suite(suite: test_case_schema.TestSuiteExecute, db: Session = Depends(get_db)):
    """
    API接口：执行一个测试套件
    """
    runner = TestRunner(db=db)
    results = runner.run_test_suite(test_case_ids=suite.test_case_ids)
    return {
        "message": "Test suite execution completed.",
        "results": results,
        "final_variables": runner.variables
    }

class TestCaseReorder(BaseModel):
    test_case_ids: List[int]

@app.post("/testcases/reorder")
def reorder_test_cases(test_case_reorder: TestCaseReorder, db: Session = Depends(get_db)):
    updated_test_cases = crud_test_case.reorder_test_cases(db=db, test_case_ids=test_case_reorder.test_case_ids)
    return {"message": "Test cases reordered successfully", "updated_count": len(updated_test_cases)}

@app.get("/")
def read_root():
    return {"Hello": "World"}