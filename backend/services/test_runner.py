import requests
import httpx
import json
import time
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from jsonpath_ng import parse

from sqlalchemy.orm import Session
from crud import crud_test_case, crud_test_suite, crud_test_report
from schemas import test_case as test_case_schema, test_report as report_schema

class TestRunner:
    def __init__(self, db: Session):
        self.db = db
        self.variables: Dict[str, Any] = {}

    def _replace_variables(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._replace_variables(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables(i) for i in data]
        elif isinstance(data, str):
            # 完整匹配，例如 "{{base_url}}/api/login"
            match = re.fullmatch(r"\{\{(\w+)\}\}(.*)", data)
            if match:
                var_name, remaining_path = match.groups()
                if var_name in self.variables:
                    base_url = self.variables[var_name]
                    # 确保基础URL和路径之间只有一个斜杠
                    return base_url.rstrip('/') + "/" + remaining_path.lstrip('/')
            
            # 如果没有找到完整匹配的变量，则进行非贪婪的部分替换
            return re.sub(r"\{\{(\w+?)\}\}", lambda m: self.variables.get(m.group(1), m.group(0)), data)

        return data

    def _extract_data(self, response_json: Dict[str, Any], rules: Optional[Dict[str, str]]):
        if not rules:
            return
        for var_name, json_path in rules.items():
            try:
                jsonpath_expr = parse(json_path)
                matches = [match.value for match in jsonpath_expr.find(response_json)]
                if matches:
                    self.variables[var_name] = matches[0]
                    print(f"✔️ 变量提取成功: {var_name} = {matches[0]}")
                else:
                    print(f"⚠️ 警告: 变量 '{var_name}' 在响应中未找到匹配项 (路径: {json_path})")
            except Exception as e:
                print(f"❌ 错误: 提取变量 '{var_name}' 失败: {e}")

    def _smart_contains(self, actual: Any, expect: Any) -> bool:
        if isinstance(expect, dict):
            if not isinstance(actual, dict):
                return False
            return all(
                k in actual and self._smart_contains(actual[k], v)
                for k, v in expect.items()
            )
        elif isinstance(expect, list):
            if not isinstance(actual, list):
                return False
            return all(
                any(self._smart_contains(actual_item, expect_item) for actual_item in actual)
                for expect_item in expect
            )
        else:
            return actual == expect

    def _execute_assertions(self, response_json: Any, response_status_code: int, assertions: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        if not assertions:
            return {"result": "success", "details": []}

        assertion_results = []
        all_passed = True

        for i, assertion in enumerate(assertions):
            check = assertion.get("check")
            comparator = assertion.get("comparator")
            expect = assertion.get("expect")
            
            actual = None
            result = "fail"
            message = ""

            try:
                if check == "status_code":
                    actual = response_status_code
                elif check == "json":
                    actual = response_json
                elif check and check.startswith("json."):
                    if not isinstance(response_json, (dict, list)):
                         raise ValueError("Response is not a valid JSON for JSONPath extraction.")
                    json_path = check[5:]
                    jsonpath_expr = parse(json_path)
                    matches = [match.value for match in jsonpath_expr.find(response_json)]
                    if matches:
                        actual = matches[0]
                    else:
                        raise ValueError(f"JSONPath '{json_path}' not found in response.")
                else:
                    raise ValueError(f"Invalid 'check' value: {check}")

                if comparator == "contains":
                    if self._smart_contains(actual, expect):
                        result = "success"
                    else:
                        message = f"Actual value does not contain expected value."
                elif comparator == "json_equals":
                    if actual == expect:
                        result = "success"
                    else:
                        message = f"Actual JSON does not strictly equal expected JSON."
                else:
                    message = f"Unknown comparator: {comparator}"
                
                if result == "fail" and not message:
                    message = f"Assertion failed: Actual value '{actual}' did not satisfy condition '{comparator}' with expected value '{expect}'"

            except Exception as e:
                message = f"Assertion execution error: {e}"

            if result == "fail":
                all_passed = False

            assertion_results.append({
                "check": check, "comparator": comparator, "expect": expect,
                "actual": actual, "result": result, "message": message
            })
        
        final_result = "success" if all_passed else "fail"
        print(f"  - 断言结果: {final_result.upper()}")
        return {"result": final_result, "details": assertion_results}

    def run_test_case(self, test_case: test_case_schema.TestCase) -> Dict[str, Any]:
        start_time = datetime.now()
        url = self._replace_variables(test_case.url)
        headers = self._replace_variables(test_case.headers)
        body = self._replace_variables(test_case.body)

        try:
            request_kwargs = {
                "method": test_case.method,
                "url": url,
                "headers": headers,
                "timeout": 10
            }
        
            if body:
                # 检查 'Content-Type' header 来决定请求体格式
                content_type = headers.get("Content-Type", "").lower()
                if "application/json" in content_type:
                    request_kwargs["json"] = body
                else:
                    request_kwargs["data"] = body
        
            response = httpx.request(**request_kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            response.raise_for_status()
            response_json = None
            try: 
                response_json = response.json()
            except json.JSONDecodeError: 
                pass

            print(f"✅ 用例 '{test_case.name}' 请求成功")
            print(f"  - Status Code: {response.status_code}")
            
            # --- FIX STARTS HERE ---
            # 使用 response_json 或 response.text 来打印响应
            response_to_print = response_json if response_json is not None else response.text
            try:
                # 尝试格式化打印JSON
                print(f"  - Response: {json.dumps(response_to_print, indent=2, ensure_ascii=False)}")
            except TypeError:
                # 如果不是JSON，直接打印文本
                print(f"  - Response: {response_to_print}")
            # --- FIX ENDS HERE ---

            self._extract_data(response_json, test_case.extract_rules)

            assertions_result = self._execute_assertions(response_json, response.status_code, test_case.assertions)

            final_status = assertions_result["result"]
            
            return {
                "id": test_case.id,
                "name": test_case.name,
                "status": final_status, 
                "status_code": response.status_code,
                "response": response_json or response.text,
                "assertions": assertions_result,
                "url": url,
                "method": test_case.method,
                "start_time": start_time,
                "duration": duration,
                "request_headers": headers,
                "request_body": body,
                "response_headers": dict(response.headers),
                "response_body": response.text
            }

        except httpx.RequestError as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"❌ 用例 '{test_case.name}' 请求失败: {e}")
            return {
                "id": test_case.id,
                "name": test_case.name,
                "status": "error",
                "response": str(e),
                "url": url,
                "method": test_case.method,
                "start_time": start_time,
                "duration": duration,
                "request_headers": headers,
                "request_body": body,
                "error_message": str(e)
            }

    def run_test_suite(self, test_case_ids: List[int]) -> List[Dict[str, Any]]:
        results = []
        for case_id in test_case_ids:
            db_case = crud_test_case.get_test_case(self.db, test_case_id=case_id)
            if db_case:
                result = self.run_test_case(db_case)
                results.append(result)
            else:
                results.append({
                    "id": case_id,
                    "name": "Unknown",
                    "status": "error",
                    "response": f"Test case with id {case_id} not found."
                })
        print("="*50)
        print("▶️ 测试套件执行完毕")
        return results

    def run_full_suite(self, suite_id: int, parent_report_id: Optional[int] = None) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """
        执行完整的测试套件（包含用例、模块、子套件）
        返回: (results, report_id)
        """
        suite = crud_test_suite.get_test_suite(self.db, test_suite_id=suite_id)
        if not suite:
            return [{
                "id": suite_id,
                "name": "Unknown Suite",
                "status": "error",
                "response": f"Test suite with id {suite_id} not found."
            }], None

        # 创建或使用现有报告
        report_id = parent_report_id
        is_root_execution = False
        if report_id is None:
            is_root_execution = True
            report_create = report_schema.TestReportCreate(
                suite_id=suite.id,
                suite_name=suite.name,
                start_time=datetime.now(),
                status="running"
            )
            report = crud_test_report.create_test_report(self.db, report_create)
            report_id = report.id

        results = []
        print(f"🚀 开始执行套件: {suite.name}")

        # 遍历 items，它们已经按照 sort_order 排序（由 SQLAlchemy relationship 保证）
        if suite.items:
            for item in suite.items:
                try:
                    if item.item_type == "test_case":
                        if item.test_case:
                            result = self.run_test_case(item.test_case)
                            self._record_result(report_id, result)
                            results.append(result)
                        else:
                            results.append({
                                "id": item.test_case_id,
                                "name": "Missing Case",
                                "status": "error",
                                "response": f"Test case ID {item.test_case_id} not found"
                            })
                    
                    elif item.item_type == "test_module":
                        if item.module:
                            print(f"  📂 执行模块: {item.module.name}")
                            if hasattr(item.module, 'test_cases') and item.module.test_cases:
                                for case in item.module.test_cases:
                                    result = self.run_test_case(case)
                                    self._record_result(report_id, result)
                                    results.append(result)
                            else:
                                pass
                        else:
                             results.append({
                                "id": item.module_id,
                                "name": "Missing Module",
                                "status": "error",
                                "response": f"Module ID {item.module_id} not found"
                            })

                    elif item.item_type == "test_suite":
                        if item.child_suite_id:
                            # 递归执行子套件
                            sub_results, _ = self.run_full_suite(item.child_suite_id, parent_report_id=report_id)
                            results.extend(sub_results)
                
                except Exception as e:
                    results.append({
                        "name": f"Error executing item {item.id}",
                        "status": "error",
                        "response": str(e)
                    })
        
        if is_root_execution:
            self._finalize_report(report_id, results)

        return results, report_id

    def _record_result(self, report_id: int, result: Dict[str, Any]):
        try:
            record_create = report_schema.TestRecordCreate(
                report_id=report_id,
                test_case_id=result.get("id"),
                case_name=result.get("name"),
                start_time=result.get("start_time"),
                duration=result.get("duration"),
                status=result.get("status"),
                url=result.get("url"),
                method=result.get("method"),
                status_code=result.get("status_code"),
                request_headers=result.get("request_headers"),
                request_body=result.get("request_body"),
                response_headers=result.get("response_headers"),
                response_body=result.get("response_body"),
                error_message=result.get("error_message"),
                assertion_results=result.get("assertions", {}).get("details")
            )
            crud_test_report.create_test_record(self.db, record_create)
        except Exception as e:
            print(f"❌ 记录测试结果失败: {e}")

    def _finalize_report(self, report_id: int, results: List[Dict[str, Any]]):
        total = len(results)
        pass_count = sum(1 for r in results if r.get("status") == "success")
        fail_count = sum(1 for r in results if r.get("status") == "fail")
        error_count = sum(1 for r in results if r.get("status") == "error")
        
        status = "success" if fail_count == 0 and error_count == 0 else "failed"
        
        report_update = report_schema.TestReportUpdate(
            end_time=datetime.now(),
            duration=0, # Calculation needed if start time persisted or fetched
            total_cases=total,
            pass_count=pass_count,
            fail_count=fail_count,
            error_count=error_count,
            status=status
        )
        
        # Calculate duration correctly by fetching report start time or just diffing now
        # Ideally fetch report to get start_time
        db_report = crud_test_report.get_test_report(self.db, report_id)
        if db_report and db_report.start_time:
            report_update.duration = (datetime.now() - db_report.start_time).total_seconds()
            
        crud_test_report.update_test_report(self.db, report_id, report_update)