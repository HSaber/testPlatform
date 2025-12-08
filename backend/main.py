from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from core.database import SessionLocal, engine, Base
from models import test_case as test_case_model
from models import test_module as test_module_model
from crud import crud_test_case, crud_test_module
from schemas import test_case as test_case_schema
from schemas import test_module as test_module_schema
from services.test_runner import TestRunner
from typing import List
from pydantic import BaseModel
from schemas import test_suite as test_suite_schema
from crud import crud_test_suite
from crud import crud_test_report
from schemas import test_report as test_report_schema

test_case_model.Base.metadata.create_all(bind=engine)
test_module_model.Base.metadata.create_all(bind=engine)

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

@app.get("/testcases/list", response_model=List[test_case_schema.TestCase])
def read_test_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    test_cases = crud_test_case.get_test_cases(db, skip=skip, limit=limit)
    return test_cases

@app.get("/testcases/{test_case_id}", response_model=test_case_schema.TestCase)
def read_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """
    获取单个测试用例详情
    """
    db_test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return db_test_case

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
def batch_delete_test_cases(batch: test_case_schema.TestCaseBatchDelete, db: Session = Depends(get_db)):
    crud_test_case.batch_delete_test_cases(db, batch.test_case_ids)


@app.post("/testcases/debug", response_model=test_case_schema.TestCaseDebugResponse)
def debug_test_case(test_case: test_case_schema.TestCaseDebugRequest, db: Session = Depends(get_db)):
    runner = TestRunner(db)
    return runner.debug_test_case(test_case)


@app.post("/testcases/copy/{test_case_id}", response_model=test_case_schema.TestCase)
def copy_test_case(test_case_id: int, db: Session = Depends(get_db)):
    db_test_case = crud_test_case.copy_test_case(db, test_case_id=test_case_id)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return db_test_case

@app.post("/testsuites/execute")
def execute_test_suite(suite: test_case_schema.TestSuiteExecute, db: Session = Depends(get_db)):
    runner = TestRunner(db)
    # 修复调用，传递 report_id=None 或者让其默认
    results, report_id = runner.run_full_suite(suite.suite_id)
    
    return {
        "message": "Test suite execution completed.",
        "results": results,
        "final_variables": runner.variables
    }

# 修改路由：ID 放在最后
@app.post("/suites/debug/{suite_id}", response_model=test_suite_schema.TestSuiteDebugResponse)
def debug_test_suite(suite_id: int, body: test_suite_schema.TestSuiteDebugBody, db: Session = Depends(get_db)):
    runner = TestRunner(db)
    return runner.debug_test_suite(suite_id, body.include_case_ids)

class TestCaseReorder(BaseModel):
    test_case_ids: List[int]

@app.post("/testcases/reorder")
def reorder_test_cases(test_case_reorder: TestCaseReorder, db: Session = Depends(get_db)):
    updated_test_cases = crud_test_case.reorder_test_cases(db=db, test_case_ids=test_case_reorder.test_case_ids)
    return {"message": "Test cases reordered successfully", "updated_count": len(updated_test_cases)}

# --- Test Modules API ---

@app.post("/modules/", response_model=test_module_schema.TestModule)
def create_module(module: test_module_schema.TestModuleCreate, db: Session = Depends(get_db)):
    return crud_test_module.create_test_module(db=db, module=module)

@app.get("/modules/", response_model=List[test_module_schema.TestModule])
def read_modules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_test_module.get_test_modules(db=db, skip=skip, limit=limit)

@app.get("/modules/{module_id}", response_model=test_module_schema.TestModule)
def read_module(module_id: int, db: Session = Depends(get_db)):
    db_module = crud_test_module.get_test_module(db, module_id=module_id)
    if db_module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    return db_module

@app.put("/modules/{module_id}", response_model=test_module_schema.TestModule)
def update_module(module_id: int, module: test_module_schema.TestModuleUpdate, db: Session = Depends(get_db)):
    db_module = crud_test_module.update_test_module(db=db, module_id=module_id, module=module)
    if db_module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    return db_module

@app.delete("/modules/{module_id}", response_model=test_module_schema.TestModule)
def delete_module(module_id: int, db: Session = Depends(get_db)):
    db_module = crud_test_module.delete_test_module(db=db, module_id=module_id)
    if db_module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    return db_module


@app.get("/")
def read_root():
    return {"Hello": "World"}

# ------------------------------------------------------------------------------
# Test Suites API
# ------------------------------------------------------------------------------

@app.post("/suites/", response_model=test_suite_schema.TestSuite)
def create_test_suite(test_suite: test_suite_schema.TestSuiteCreate, db: Session = Depends(get_db)):
    return crud_test_suite.create_test_suite(db=db, test_suite=test_suite)

@app.get("/suites/", response_model=List[test_suite_schema.TestSuite])
def read_test_suites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_test_suite.get_test_suites(db, skip=skip, limit=limit)

@app.get("/suites/{test_suite_id}", response_model=test_suite_schema.TestSuite)
def read_test_suite(test_suite_id: int, db: Session = Depends(get_db)):
    db_test_suite = crud_test_suite.get_test_suite(db, test_suite_id=test_suite_id)
    if db_test_suite is None:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return db_test_suite

@app.put("/suites/{test_suite_id}", response_model=test_suite_schema.TestSuite)
def update_test_suite(test_suite_id: int, test_suite: test_suite_schema.TestSuiteUpdate, db: Session = Depends(get_db)):
    db_test_suite = crud_test_suite.update_test_suite(db, test_suite_id=test_suite_id, test_suite=test_suite)
    if db_test_suite is None:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return db_test_suite

@app.delete("/suites/{test_suite_id}", response_model=test_suite_schema.TestSuite)
def delete_test_suite(test_suite_id: int, db: Session = Depends(get_db)):
    db_test_suite = crud_test_suite.delete_test_suite(db, test_suite_id=test_suite_id)
    if db_test_suite is None:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return db_test_suite

@app.post("/suites/run/{test_suite_id}")
def run_test_suite_endpoint(test_suite_id: int, db: Session = Depends(get_db)):
    runner = TestRunner(db=db)
    results, report_id = runner.run_full_suite(suite_id=test_suite_id)
    
    # 检查是否因为找不到套件而返回错误
    if len(results) == 1 and results[0].get("name") == "Unknown Suite":
        raise HTTPException(status_code=404, detail=results[0].get("response"))

    return {
        "message": "Test suite execution completed.",
        "results": results,
        "final_variables": runner.variables,
        "report_id": report_id
    }

@app.get("/reports/list", response_model=List[test_report_schema.TestReport])
def read_test_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取测试报告列表
    """
    test_reports = crud_test_report.get_test_reports(db, skip=skip, limit=limit)
    return test_reports

@app.get("/reports/{report_id}", response_model=test_report_schema.TestReport)
def read_test_report(report_id: int, db: Session = Depends(get_db)):
    """
    获取特定测试报告的详细信息
    """
    db_report = crud_test_report.get_test_report(db, test_report_id=report_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Test report not found")
    return db_report