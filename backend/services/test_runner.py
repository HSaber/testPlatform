import requests
import httpx
import json
import time
import re
import io
import contextlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from jsonpath_ng import parse

from sqlalchemy.orm import Session
from crud import crud_test_case, crud_test_suite, crud_test_report
from schemas import test_case as test_case_schema, test_report as report_schema
from models import test_case as test_case_models
from core.config import API_BASE_URL
import traceback # 新增导入

class TestRunner:
    def __init__(self, db: Session):
        self.db = db
        self.variables: Dict[str, Any] = {}
        # 初始化一个 Client 实例用于保持会话（Cookies）
        # FIX: 设置 base_url 以支持相对路径 URL
        self.client = httpx.Client(verify=False, base_url=API_BASE_URL)

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

    # Fix: 更新类型提示以支持 list 类型的响应
    def _extract_data(self, response_json: Union[Dict[str, Any], List[Any]], rules: Optional[Dict[str, str]]) -> Dict[str, Any]:
        extracted = {}
        if not rules:
            return extracted
        for var_name, json_path in rules.items():
            try:
                jsonpath_expr = parse(json_path)
                matches = [match.value for match in jsonpath_expr.find(response_json)]
                if matches:
                    self.variables[var_name] = matches[0]
                    extracted[var_name] = matches[0]
                    print(f"✔️ 变量提取成功: {var_name} = {matches[0]}")
                else:
                    print(f"⚠️ 警告: 变量 '{var_name}' 在响应中未找到匹配项 (路径: {json_path})")
            except Exception as e:
                print(f"❌ 错误: 提取变量 '{var_name}' 失败: {e}")
        return extracted

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

    def _execute_script(self, script: str, context: Dict[str, Any]):
        """执行 Python 脚本"""
        if not script or not script.strip():
            return

        try:
            print(f"[Script] Executing script...\n{script[:100]}...")
            # 定义脚本可用的全局变量
            safe_globals = {
                "__builtins__": __builtins__,
                "variables": self.variables,  # 允许读写变量
                "print": print,
                "json": __import__("json"),
                "random": __import__("random"),
                "time": __import__("time"),
                "datetime": __import__("datetime"),
            }
            # 将上下文合并到局部变量
            local_vars = context.copy()
            
            exec(script, safe_globals, local_vars)
            
            print("[Script] Execution success.")
        except Exception as e:
            print(f"[Script] Execution failed: {e}")
            traceback.print_exc()
            raise e

    def run_test_case(self, test_case: test_case_schema.TestCase) -> Dict[str, Any]:
        start_time = datetime.now()

        # 1. 执行前置脚本
        if hasattr(test_case, 'setup_script') and test_case.setup_script:
            try:
                context = {
                    "url": test_case.url,
                    "method": test_case.method,
                    "headers": test_case.headers,
                    "body": test_case.body
                }
                self._execute_script(test_case.setup_script, context)
            except Exception as e:
                return {
                    "id": test_case.id,  # Ensure ID is included
                    "name": test_case.name,
                    "status": "error",
                    "duration": (datetime.now() - start_time).total_seconds(),
                    "error_message": f"Setup script failed: {str(e)}",
                    "response": None,
                    "assertions": {"result": "error", "details": []}  # Fix: Changed [] to dict
                }

        url = self._replace_variables(test_case.url)

        # 1.1 处理 URL
        if not url.startswith("http"):
            url = f"{API_BASE_URL.rstrip('/')}/{url.lstrip('/')}"

        # 1.2 处理 Headers
        headers = {"Content-Type": "application/json"}
        if test_case.headers:
            # 替换 headers 中的变量
            processed_headers = self._replace_variables(test_case.headers)
            if isinstance(processed_headers, dict):
                headers.update(processed_headers)

        # 1.3 处理 Body
        body = None
        if test_case.body:
            # 替换 body 中的变量
            body = self._replace_variables(test_case.body)
        
        # 打印请求详情
        print(f"\n--- Request Info ---")
        print(f"Method: {test_case.method}")
        print(f"URL: {url}")
        print(f"Headers: {json.dumps(headers, ensure_ascii=False)}")
        print(f"Body: {json.dumps(body, ensure_ascii=False) if body else 'None'}")
        print(f"--------------------\n")

        try:
            # 发送请求
            # FIX: 根据 Content-Type 决定发送方式
            content_type = headers.get("Content-Type", "").lower()
            if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                 response = self.client.request(test_case.method, url, headers=headers, data=body)
            else:
                 # 默认使用 JSON，除非明确指定了其他不支持 JSON 的类型（这里简化处理，默认 JSON）
                 response = self.client.request(test_case.method, url, headers=headers, json=body)
            
            # 处理响应编码
            response.encoding = "utf-8"
            
            # 尝试解析 JSON
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = response.text

            # 打印响应详情
            print(f"\n--- Response Info ---")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:1000] + '...' if len(response.text) > 1000 else response.text}")
            print(f"---------------------\n")

            # 2. 执行后置脚本 (在提取变量和断言之前，或者之后，视需求)
            # 通常建议在断言之前，以便脚本可以辅助断言或提取复杂变量
            if hasattr(test_case, 'teardown_script') and test_case.teardown_script:
                context = {
                    "response": response,
                    "response_json": response_json,
                    "status_code": response.status_code
                }
                try:
                    self._execute_script(test_case.teardown_script, context)
                except Exception as e:
                     return {
                        "id": test_case.id,  # Ensure ID is included
                        "name": test_case.name,
                        "status": "error",
                        "duration": (datetime.now() - start_time).total_seconds(),
                        "error_message": f"Teardown script failed: {str(e)}",
                        "response": {
                            "status_code": response.status_code,
                            "headers": dict(response.headers),
                            "body": response_json
                        },
                        "assertions": {"result": "error", "details": []}  # Fix: Changed [] to dict
                    }

            # 3. 提取变量
            # Fix: 允许 response_json 为 list，以便能从数组响应中提取数据
            extracted_data = {} # 初始化为空字典
            if response_json is not None and isinstance(response_json, (dict, list)):
                extracted_data = self._extract_data(response_json, test_case.extract_rules)

            # 4. 执行断言
            assertion_result = {}
            if response and test_case.assertions:
                # Fix: 同样允许断言检查 list 类型的响应
                resp_json = response_json if isinstance(response_json, (dict, list)) else {}
                assertion_result = self._execute_assertions(resp_json, response.status_code, test_case.assertions)
                
            final_status = assertion_result.get("result", "success") # 如果没有断言，默认为成功
            duration = (datetime.now() - start_time).total_seconds()

            test_result = {
                "id": test_case.id,
                "name": test_case.name,
                "status": final_status, 
                "status_code": response.status_code,
                "response": response_json or response.text,
                "assertions": assertion_result,
                "extract_results": extracted_data,
                "url": url,
                "method": test_case.method,
                "start_time": start_time,
                "duration": duration,
                "request_headers": headers,
                "request_body": body,
                "response_headers": dict(response.headers),
                "response_body": response.text
            }

            return test_result

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
                "error_message": str(e),
                "assertions": {"result": "error", "details": []}  # Fix: Added assertions field
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

    def debug_test_case(self, test_case_data: test_case_schema.TestCaseCreate) -> test_case_schema.TestCaseDebugResponse:
        start_time = time.time()
        logs_capture = io.StringIO()
        
        # 捕获标准输出
        with contextlib.redirect_stdout(logs_capture):
            print(f"开始调试测试用例: {test_case_data.name}")
            
            # 1. 替换变量
            url = self._replace_variables(test_case_data.url)
            # FIX: 使用正确的字段名 headers 和 body
            headers = self._replace_variables(test_case_data.headers) if test_case_data.headers else {}
            body = self._replace_variables(test_case_data.body) if test_case_data.body else None
            
            # 处理 body 为 JSON 的情况
            if body and isinstance(body, str):
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    pass

            # 2. 执行前置脚本
            if test_case_data.setup_script:
                print("正在执行前置脚本...")
                self._execute_script(test_case_data.setup_script)

            # 3. 发送请求
            method = test_case_data.method.upper()
            response = None
            error_message = None
            response_body = None
            response_headers = None
            status_code = None
            
            try:
                # FIX: 根据 Content-Type 决定发送方式
                content_type = headers.get("Content-Type", "").lower() if headers else ""
                use_data = "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type

                if method == "GET":
                    response = self.client.get(url, headers=headers, params=body)
                elif method == "POST":
                    if use_data:
                        response = self.client.post(url, headers=headers, data=body)
                    else:
                        response = self.client.post(url, headers=headers, json=body)
                elif method == "PUT":
                    if use_data:
                        response = self.client.put(url, headers=headers, data=body)
                    else:
                        response = self.client.put(url, headers=headers, json=body)
                elif method == "DELETE":
                    response = self.client.delete(url, headers=headers, params=body)
                else:
                    raise ValueError(f"不支持的请求方法: {method}")
                
                status_code = response.status_code
                response_headers = dict(response.headers)
                
                try:
                    response_body = response.json()
                except:
                    response_body = response.text
                
                print(f"请求成功: {method} {url} - Status: {status_code}")
                
            except Exception as e:
                error_message = str(e)
                print(f"请求失败: {e}")
                traceback.print_exc()

            # 4. 执行后置脚本
            if test_case_data.teardown_script:
                print("正在执行后置脚本...")
                try:
                    # 如果有响应，将其注入到脚本上下文中
                    context = {}
                    if response:
                         context = {"response": response}
                         
                    self._execute_script(test_case_data.teardown_script, context)
                except Exception as e:
                     print(f"后置脚本执行失败: {e}")
                     traceback.print_exc()

            # 5. 提取变量
            extracted_data = {}
            if response_body is not None and isinstance(response_body, (dict, list)):
                print(f"🔍 [Debug] 开始提取变量: 规则={test_case_data.extract_rules}, 响应类型={type(response_body)}")
                extracted_data = self._extract_data(response_body, test_case_data.extract_rules)

            # 6. 执行断言
            assertion_result = {}
            if response and test_case_data.assertions:
                # Fix: 允许 list 类型响应进行断言
                resp_json = response_body if isinstance(response_body, (dict, list)) else {}
                assertion_result = self._execute_assertions(resp_json, response.status_code, test_case_data.assertions)

        duration = time.time() - start_time
        logs = logs_capture.getvalue()
        logs_capture.close()
        # 在 return 之前，确保 url 和 method 是可用的
        # 注意：debug_test_case 方法内部拼接了 url，所以这里直接使用拼接后的 url 变量
        # method 也是局部变量

        return test_case_schema.TestCaseDebugResponse(
            status="SUCCESS" if not error_message else "FAILED",
            status_code=status_code,
            response=response_body,
            assertions=assertion_result,
            logs=logs,
            duration=duration,
            request_headers=headers,
            request_body=body,
            response_headers=response_headers,
            # 新增字段
            url=url,
            method=method,
            # 添加提取变量结果
            extract_results=extracted_data
        )

    def run_full_suite(self, suite_id: int, parent_report_id: int = None):
        """
        执行完整的测试套件（包含用例、模块、子套件）
        返回: (results, report_id)
        """
        suite = crud_test_suite.get_test_suite(self.db, test_suite_id=suite_id)
        if not suite:
            raise ValueError(f"Test suite {suite_id} not found")

        # 创建或使用父报告
        if parent_report_id:
            report_id = parent_report_id
        else:
            # 顶层套件执行，创建新报告
            # FIX: 添加 suite_name
            report = crud_test_report.create_test_report(self.db, report_schema.TestReportCreate(
                suite_id=suite.id,
                suite_name=suite.name,
                status="running"
            ))
            report_id = report.id

        results = []
        
        # 遍历 items
        if suite.items:
            for item in suite.items:
                try:
                    if item.item_type == "test_case":
                        if item.test_case:
                            result = self.run_test_case(item.test_case)
                            # result['id'] = item.test_case.id # run_test_case 已经包含 id
                            self._record_result(report_id, result)
                            results.append(result)

                    elif item.item_type == "test_module":
                        if item.module:
                            # 递归执行模块中的用例
                            if item.module.test_cases:
                                for case in item.module.test_cases:
                                    result = self.run_test_case(case)
                                    self._record_result(report_id, result)
                                    results.append(result)

                    elif item.item_type == "test_suite":
                        # 递归执行子套件
                        if item.child_suite_id:
                            sub_results, _ = self.run_full_suite(item.child_suite_id, parent_report_id=report_id)
                            results.extend(sub_results)

                except Exception as e:
                    results.append({
                        "name": f"Error executing item {item.id}",
                        "status": "error",
                        "response": str(e)
                    })
        
        if parent_report_id is None:
            self._finalize_report(report_id, results)

        return results, report_id

    def _record_result(self, report_id: int, result: Dict[str, Any]):
        """记录单个测试用例的执行结果"""
        try:
            # 处理断言结果
            assertion_details = None
            if result.get("assertions") and isinstance(result["assertions"], dict):
                assertion_details = result["assertions"].get("details")

            # 处理响应体，确保为字符串
            resp_body = result.get("response_body")
            if isinstance(resp_body, (dict, list)):
                resp_body = json.dumps(resp_body, ensure_ascii=False)
            elif resp_body is None:
                # 兼容旧逻辑，如果没有 response_body，尝试使用 response 字段
                resp = result.get("response")
                if isinstance(resp, (dict, list)):
                    resp_body = json.dumps(resp, ensure_ascii=False)
                else:
                    resp_body = str(resp) if resp is not None else None

            crud_test_report.create_test_record(self.db, report_schema.TestRecordCreate(
                report_id=report_id,
                test_case_id=result.get("id"),
                case_name=result.get("name", "Unknown Case"),
                status=result.get("status", "error"),
                duration=result.get("duration", 0.0),
                # FIX: 映射详细信息
                url=result.get("url"),
                method=result.get("method"),
                status_code=result.get("status_code"),
                request_headers=result.get("request_headers"),
                request_body=result.get("request_body"),
                response_headers=result.get("response_headers"),
                response_body=resp_body,
                error_message=result.get("error_message"),
                assertion_results=assertion_details
            ))
        except Exception as e:
            print(f"Failed to record result: {e}")

    def _finalize_report(self, report_id: int, results: List[Dict[str, Any]]):
        """更新测试报告的最终状态"""
        total = len(results)
        # FIX: 状态判断逻辑统一，假设 run_test_case 返回 'success' 表示通过
        passed = sum(1 for r in results if r.get("status") == "success")
        failed = total - passed
        
        # 计算总耗时
        total_duration = sum(r.get("duration", 0.0) for r in results)

        final_status = "success" if failed == 0 else "failed"

        crud_test_report.update_test_report(self.db, report_id, report_schema.TestReportUpdate(
            status=final_status,
            total_cases=total,
            pass_count=passed,   # FIX: 使用正确的字段名 pass_count
            fail_count=failed,   # FIX: 使用正确的字段名 fail_count
            duration=total_duration,
            end_time=datetime.now()
        ))

    def debug_test_suite(self, suite_id: int, include_case_ids: List[int] = None):
        """
        调试执行测试套件，不记录到数据库，支持过滤用例
        """
        suite = crud_test_suite.get_test_suite(self.db, test_suite_id=suite_id)
        if not suite:
             return {
                 "suite_id": suite_id,
                 "suite_name": "Unknown",
                 "results": [],
                 "total_duration": 0
             }

        results = []
        start_time = time.time()

        if suite.items:
            for item in suite.items:
                try:
                    if item.item_type == "test_case":
                        if item.test_case:
                            # 如果指定了 include_case_ids 且当前用例不在其中，则跳过
                            if include_case_ids is not None and item.test_case.id not in include_case_ids:
                                continue
                            
                            debug_result = self.debug_test_case(item.test_case)
                            res_dict = debug_result.dict()
                            res_dict['id'] = item.test_case.id
                            res_dict['name'] = item.test_case.name
                            results.append(res_dict)
                    
                    elif item.item_type == "test_module":
                        if item.module and item.module.test_cases:
                            for case in item.module.test_cases:
                                if include_case_ids is not None and case.id not in include_case_ids:
                                    continue
                                
                                debug_result = self.debug_test_case(case)
                                res_dict = debug_result.dict()
                                res_dict['id'] = case.id
                                res_dict['name'] = case.name
                                results.append(res_dict)

                    # 注意：当前简单的调试模式暂不递归处理子套件的筛选，
                    # 除非前端传递所有层级的用例ID。这里暂只处理当前套件直属的用例和模块内的用例。
                
                except Exception as e:
                    results.append({
                        "status": "error",
                        "error_message": str(e)
                    })

        return {
            "suite_id": suite.id,
            "suite_name": suite.name,
            "results": results,
            "total_duration": time.time() - start_time
        }