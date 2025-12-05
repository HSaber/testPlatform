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
        # 初始化一个 Client 实例用于保持会话（Cookies）
        self.client = httpx.Client(verify=False)

    def _replace_variables(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._replace_variables(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables(i) for i in data]
        elif isinstance(data, str):
            # 检查是否仅包含一个变量，例如 "{{token}}"
            full_match = re.fullmatch(r"\{\{(\w+)\}\}", data)
            if full_match:
                var_name = full_match.group(1)
                if var_name in self.variables:
                    return self.variables[var_name]
            
            # 对于其他情况，进行字符串替换，不再尝试智能添加斜杠
            return re.sub(r"\{\{(\w+?)\}\}", lambda m: str(self.variables.get(m.group(1), m.group(0))), data)

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
            # 优先进行严格比较
            if actual == expect:
                return True
            # 弱类型比较补救：都转为字符串再比 (解决 0 匹配 "0" 的问题)
            return str(actual) == str(expect)

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
                         # 如果响应不是JSON，但用户尝试提取JSON字段，应该视为提取失败，而不是报错中断
                         actual = None
                         message = "Response is not a valid JSON object"
                    else:
                        json_path = check[5:]
                        jsonpath_expr = parse(json_path)
                        matches = [match.value for match in jsonpath_expr.find(response_json)]
                        if matches:
                            actual = matches[0]
                        else:
                            # 路径不存在时，actual保持None
                            message = f"JSONPath '{json_path}' not found in response."
                else:
                    raise ValueError(f"Invalid 'check' value: {check}")

                # 辅助函数：安全转换为字符串
                def safe_str(val):
                    if isinstance(val, (dict, list)):
                        try:
                            return json.dumps(val, ensure_ascii=False)
                        except:
                            return str(val)
                    return str(val)

                # 执行比较逻辑
                if comparator == "contains":
                    if actual is not None and self._smart_contains(actual, expect):
                        result = "success"
                    else:
                        message = f"Actual value does not contain expected value."
                elif comparator in ["equals", "==", "="]:
                    # 增强的弱类型比较逻辑
                    # 1. 严格相等
                    if actual == expect:
                        result = "success"
                    # 2. 转换为字符串比较 (处理 0 == "0")
                    elif str(actual) == str(expect):
                        result = "success"
                    else:
                        # 3. 尝试转换为浮点数比较 (处理 1 == 1.0)
                        try:
                            if float(actual) == float(expect):
                                result = "success"
                        except (ValueError, TypeError):
                            pass

                    if result != "success":
                        message = f"Actual '{actual}' does not equal Expected '{expect}'"

                elif comparator == "json_equals":
                    if actual == expect:
                        result = "success"
                    else:
                        message = f"Actual JSON does not strictly equal expected JSON."
                elif comparator in ["!=", "not_equals"]:
                    if str(actual) != str(expect):
                        result = "success"
                    else:
                        message = f"Actual '{actual}' equals Expected '{expect}' (should not)"
                # 可以根据需要添加更多比较器，如 gt, lt 等
                else:
                    message = f"Unknown or unsupported comparator: {comparator}"
                
                # 如果上面没有设置成功，且没有特定错误消息，生成默认错误消息
                if result == "fail" and not message:
                    message = f"Assertion failed: Actual '{actual}' vs Expected '{expect}' ({comparator})"

                # 打印断言详情用于调试
                print(f"    [Assert] Check: {check}, Comparator: {comparator}")
                print(f"      Expect: {expect} (Type: {type(expect).__name__})")
                print(f"      Actual: {actual} (Type: {type(actual).__name__})")
                print(f"      Result: {result.upper()}")

                # 记录结果，确保 expect 和 actual 都是字符串格式
                assertion_results.append({
                    "check": check, "comparator": comparator, 
                    "expect": safe_str(expect),
                    "actual": safe_str(actual),
                    "result": result, "message": message
                })

            except Exception as e:
                message = f"Assertion execution error: {e}"
                assertion_results.append({
                    "check": check, "comparator": comparator, "expect": str(expect),
                    "actual": str(actual) if 'actual' in locals() else "None",
                    "result": "fail", "message": message
                })

            if result == "fail":
                all_passed = False
        
        final_result = "success" if all_passed else "fail"
        print(f"  - 断言结果: {final_result.upper()}")
        return {"result": final_result, "details": assertion_results}

    def run_test_case(self, test_case: test_case_schema.TestCase) -> Dict[str, Any]:
        start_time = datetime.now()
        url = self._replace_variables(test_case.url)
        
        # 1. 定义默认 Headers (模拟浏览器行为)
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        
        # 2. 处理用户自定义 Headers
        custom_headers = self._replace_variables(test_case.headers) or {}
        
        # 3. 合并 Headers (用户自定义覆盖默认)
        headers = {**default_headers, **custom_headers}
        
        # DEBUG: 打印最终合并后的 Headers，用于排查 Authorization 丢失等问题
        print(f"  -> Request Headers: {json.dumps(headers, indent=2, ensure_ascii=False)}")

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
        
            # 使用 self.client.request 替代 httpx.request 以自动处理 Cookies
            response = self.client.request(**request_kwargs)
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
            # 确保 response_body 是字符串
            resp_body = result.get("response_body")
            if not isinstance(resp_body, str):
                if resp_body is None:
                    resp_body = ""
                else:
                    try:
                        resp_body = json.dumps(resp_body, ensure_ascii=False)
                    except:
                        resp_body = str(resp_body)

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
                response_body=resp_body,
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