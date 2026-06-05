# backend/api.py
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse
import yaml

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session  # Import Session
from typing import Any, Dict, List # 新增导入 List
import json
import os
import httpx # 新增导入 httpx
import re # 新增导入 re
import traceback # 新增导入 traceback

from backend.core.database import get_db # 导入 get_db
from backend.core.config import DEEPSEEK_API_URL, DEEPSEEK_API_KEY # 导入 DeepSeek 配置
from backend.crud.crud_test_case import crud_test_case
from backend.schemas.test_case import TestCaseCreate
from backend.schemas.api_schemas import OpenApiSpecInput # 新增导入
from backend.models.test_case import TestCase as DBTestCase


router = APIRouter()

# Helper to generate example from schema
def generate_example_from_schema(schema: dict, openapi_spec: dict = None, seen_refs: set = None) -> Any:
    """递归地从 OpenAPI/JSON Schema 中生成一个示例值，处理 $ref 和循环引用。"""
    if seen_refs is None:
        seen_refs = set()

    if "$ref" in schema:
        ref_path = schema["$ref"]
        if ref_path in seen_refs:
            # 检测到循环引用，返回一个占位符或停止递归
            return f"_CircularRef_:{ref_path.split('/')[-1]}"
        
        seen_refs.add(ref_path)
        # 解析 $ref，通常是 #/components/schemas/MySchema
        # 简化处理，假设路径是 #/components/schemas/Name
        # 实际生产环境需要更健壮的解析逻辑
        try:
            parts = ref_path.split('/')
            if len(parts) >= 3 and parts[0] == '#':
                # 假设是 #/components/schemas/Name
                current_schema = openapi_spec
                for part in parts[1:]:
                    if current_schema and part in current_schema:
                        current_schema = current_schema[part]
                    else:
                        current_schema = None
                        break
                if current_schema:
                    # 递归调用，传递 openapi_spec 和更新 seen_refs
                    return generate_example_from_schema(current_schema, openapi_spec, seen_refs)
            return f"_RefNotFound_:{ref_path}"
        except Exception as e:
            return f"_RefError_:{ref_path} ({e})"

    _type = schema.get("type")
    _format = schema.get("format")
    _enum = schema.get("enum")
    _default = schema.get("default")
    _example = schema.get("example")

    if _example is not None:
        return _example
    if _default is not None:
        return _default
    if _enum:
        return _enum[0] # 返回枚举的第一个值

    if _type == "string":
        if _format == "date":
            return "2023-01-01"
        if _format == "date-time":
            return "2023-01-01T12:00:00Z"
        if _format == "uuid":
            return "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        return "string_example"
    elif _type == "integer":
        return 0
    elif _type == "number":
        return 0.0
    elif _type == "boolean":
        return True
    elif _type == "array":
        items_schema = schema.get("items", {})
        return [generate_example_from_schema(items_schema, openapi_spec, seen_refs)]
    elif _type == "object":
        properties = schema.get("properties", {})
        return {k: generate_example_from_schema(v, openapi_spec, seen_refs) for k, v in properties.items()}
    elif "oneOf" in schema or "anyOf" in schema or "allOf" in schema:
        # 对于组合类型，尝试解析第一个子 schema
        if "oneOf" in schema and schema["oneOf"]:
            return generate_example_from_schema(schema["oneOf"][0], openapi_spec, seen_refs)
        if "anyOf" in schema and schema["anyOf"]:
            return generate_example_from_schema(schema["anyOf"][0], openapi_spec, seen_refs)
        if "allOf" in schema and schema["allOf"]:
            # allOf 组合类型，这里简单地取第一个子 schema 作为示例，实际可能需要更复杂的合并逻辑
            return generate_example_from_schema(schema["allOf"][0], openapi_spec, seen_refs)
    return None

def _parse_ai_json(raw_response):
    if isinstance(raw_response, list):
        return raw_response
    if isinstance(raw_response, dict):
        return raw_response
    content = raw_response.strip()

    code_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', content, re.DOTALL)
    if code_match:
        content = code_match.group(1).strip()
    elif content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    arr_match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
    if arr_match:
        try:
            return json.loads(arr_match.group())
        except json.JSONDecodeError:
            pass

    results = []
    depth = 0
    start = -1
    in_string = False
    escape = False
    for i, ch in enumerate(content):
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    obj = json.loads(content[start:i+1])
                    results.append(obj)
                except json.JSONDecodeError:
                    pass
                start = -1
    if results:
        return results

    print(f"--- _parse_ai_json 解析失败，原始内容前500字符: {content[:500]} ---")
    raise ValueError("无法解析 AI 响应中的任何 JSON 对象")

PLAN_PROMPT_TEMPLATE = """
你是一个专业的测试工程师。请分析以下 OpenAPI 接口信息，规划所有需要生成的测试用例。
对接口信息中出现的【每一个参数】（包括 query、header、path、body 中的每个字段），逐一分析并规划以下场景的用例：
- 正常值用例（提供合法有效的参数值）
- 缺失用例（不传该参数）
- 类型错误用例（传错误的数据类型）
- 边界值用例（传极值/超长字符串/特殊字符等）
另外还需规划鉴权维度用例：无鉴权头、无效 token、过期 token

请只返回一个 JSON 对象，格式如下：
{{
  "total": 数字,
  "cases": ["用例名称1", "用例名称2", ...]
}}

OpenAPI 接口信息：
路径: {path}
方法: {method}
详细信息: {details_json}
"""

BATCH_PROMPT_TEMPLATE = """
你是一个专业的测试工程师。请根据以下接口信息，生成指定列表中的测试用例详细内容。

接口信息：
路径: {path}
方法: {method}
详细信息: {details_json}

请为以下用例名称生成对应的详细测试用例 JSON：
{cases_names}

每个测试用例是一个 JSON 对象，遵循以下结构：
{{
  "name": "用例名称",
  "description": "用例描述",
  "method": "GET/POST/PUT/DELETE",
  "url": "/your/path",
  "headers": {{"Content-Type": "application/json"}},
  "body": {{}},
  "content_type": "application/json",
  "extract_rules": [],
  "assertions": []
}}

请只返回 JSON 格式的列表，不要包含任何额外解释、文字说明、Markdown 代码块标记（如 ```json）或其他非 JSON 内容。
"""

BATCH_SIZE = 10

# 调用 DeepSeek API 的辅助函数
async def call_deepseek_api(prompt_messages: List[Dict[str, str]]) -> str:
    """调用 DeepSeek API 获取测试用例。"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    payload = {
        "model": "deepseek-coder", # 或者其他 DeepSeek 模型，如 deepseek-chat
        "messages": prompt_messages,
        "temperature": 0.7,
        "max_tokens": 8192,
        "stream": False
    }

    print("--- 准备调用 DeepSeek API ---") # DEBUG
    print(f"DeepSeek API URL: {DEEPSEEK_API_URL}") # DEBUG: 打印 URL
    print(f"DeepSeek API Key (first 5 chars): {DEEPSEEK_API_KEY[:5]}...") # DEBUG: 打印 Key 前缀
    print(f"DeepSeek Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}") # DEBUG: 打印 Payload
    
    async with httpx.AsyncClient() as client:
        try:
            print("--- 尝试发送 DeepSeek API 请求 ---") # DEBUG
            response = await client.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60.0) # 增加超时时间到 60 秒
            print("--- DeepSeek API 请求已发送 ---") # DEBUG
            response.raise_for_status() # Raises HTTPStatusError for bad responses (4xx or 5xx)
            
            # 获取原始文本，无论是否能解析为 JSON
            deepseek_raw_response_text = response.text
            print("--- DeepSeek API 原始响应文本（来自 httpx.response.text）开始 ---")
            print(deepseek_raw_response_text)
            print("--- DeepSeek API 原始响应文本（来自 httpx.response.text）结束 ---")

            try:
                result = response.json() # 尝试解析为 JSON
                print("--- DeepSeek API 原始响应 JSON（来自 response.json()）开始 ---") # DEBUG: 确保打印原始响应
                print(json.dumps(result, indent=2, ensure_ascii=False)) # 打印 DeepSeek 完整 JSON 响应
                print("--- DeepSeek API 原始响应 JSON（来自 response.json()）结束 ---") # DEBUG
                
                # 假设 DeepSeek 返回的格式是 result['choices'][0]['message']['content']
                if 'choices' in result and len(result['choices']) > 0 and 'message' in result['choices'][0] and 'content' in result['choices'][0]['message']:
                    print("--- DeepSeek API 调用成功，提取到 content ---") # DEBUG
                    return result['choices'][0]['message']['content']
                else:
                    error_msg = "DeepSeek API 响应 JSON 结构不符合预期，未找到 'choices[0].message.content'"
                    print(f"--- {error_msg} ---")
                    print(f"完整响应 JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    raise ValueError(error_msg)

            except json.JSONDecodeError as e: # 专门捕获 JSON 解析错误
                print(f"--- DeepSeek API 响应 JSON 解析失败（JSONDecodeError）: {e} ---") # DEBUG
                print(f"导致解析失败的原始响应文本:\n{deepseek_raw_response_text}") # 打印导致错误的原始文本
                raise HTTPException(status_code=500, detail=f"DeepSeek API 响应 JSON 解析失败: {e}")
            
        except httpx.HTTPStatusError as e:
            print(f"--- DeepSeek API HTTP 错误: {e.response.status_code} - {e.response.text} ---") # DEBUG
            raise HTTPException(status_code=500, detail=f"DeepSeek API HTTP 错误: {e.response.status_code}")
        except httpx.RequestError as e: # 捕获更具体的请求错误
            print(f"--- DeepSeek API 请求失败（网络/连接错误）: {e} ---") # DEBUG
            raise HTTPException(status_code=500, detail=f"DeepSeek API 请求失败: {e}")
        except Exception as e:
            print(f"--- 调用 DeepSeek API 失败（通用异常）: {e} ---") # DEBUG
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"调用 DeepSeek API 失败: {e}")

# 加载 OpenAPI 规范
def load_openapi_spec(spec_content):
    """加载 OpenAPI 规范"""
    try:
        spec = json.loads(spec_content) # 假设现在是 JSON 格式
        # validate_v3_spec(spec) # Swagger 2.0 不需要验证
        return spec
    except Exception as e:
        raise ValueError(f"无法加载或验证 OpenAPI 规范: {e}")

# 根据 OpenAPI 规范生成 API 路由
def generate_api_routes(router: APIRouter, spec):
    """根据 OpenAPI 规范生成 API 路由"""
    for path, path_item in spec['paths'].items():
        for method, operation in path_item.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                # 获取操作 ID
                operation_id = operation.get('operationId')
                if not operation_id:
                    print(f"警告：缺少 operationId，为 {method.upper()} {path} 生成默认 ID")
                    operation_id = f"{method.lower()}_{path.replace('/', '_')}"

                # 定义处理函数
                async def handler(request: Request, path=path, method=method.upper(), operation=operation):
                    """处理 API 请求"""
                    print(f"处理 {method} 请求：{path}")

                    # 获取请求参数
                    if method == 'GET':
                        params = request.query_params
                    else:
                        try:
                            params = await request.json()
                        except:
                            params = await request.form()

                    # TODO: 在这里添加您的业务逻辑
                    # 1. 验证请求参数
                    # 2. 执行数据库操作
                    # 3. 构建响应数据

                    # 示例：返回一个简单的响应
                    response_data = {
                        'message': f'成功处理 {method} 请求：{path}',
                        'params': params
                    }
                    return JSONResponse(content=response_data)

                # 注册路由
                handler.__name__ = operation_id  # 设置函数名称为 operationId
                router.add_api_route(path, endpoint=handler, methods=[method.upper()])
                print(f"已添加路由：{method.upper()} {path} (operationId: {operation_id})")

@router.post("/generate_test_cases")
async def generate_test_cases_api(spec_input: OpenApiSpecInput, db: Session = Depends(get_db)):
    print("--- generate_test_cases_api 函数开始执行 ---") # DEBUG
    try:
        openapi_spec = spec_input.openapi_spec
        
        for path, path_item in openapi_spec.get("paths", {}).items():
            for method, details in path_item.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue

                print(f"--- 规划阶段: 路径 {path} 方法 {method.upper()} ---") # DEBUG
                
                try:
                    details_json = json.dumps(details, indent=2, ensure_ascii=False)
                    method_upper = method.upper()
                    
                    plan_prompt = PLAN_PROMPT_TEMPLATE.format(path=path, method=method_upper, details_json=details_json)
                    plan_messages = [
                        {"role": "system", "content": "你是一个专业的测试工程师。请只返回 JSON 格式，不要包含任何额外解释或 Markdown 标记。"},
                        {"role": "user", "content": plan_prompt}
                    ]
                    plan_raw = await call_deepseek_api(plan_messages)
                    plan = _parse_ai_json(plan_raw)
                    all_case_names = plan.get("cases", [])
                    total = len(all_case_names)
                    print(f"--- 规划完毕，共 {total} 条用例 ---") # DEBUG
                    
                    first_batch_names = all_case_names[:BATCH_SIZE]
                    cases_names_str = "\n".join(f"- {name}" for name in first_batch_names)
                    batch_prompt = BATCH_PROMPT_TEMPLATE.format(path=path, method=method_upper, details_json=details_json, cases_names=cases_names_str)
                    batch_messages = [
                        {"role": "system", "content": "你是一个专业的测试工程师。请只返回 JSON 数组格式，不要包含任何额外解释或 Markdown 标记。"},
                        {"role": "user", "content": batch_prompt}
                    ]
                    batch_raw = await call_deepseek_api(batch_messages)
                    test_cases = _parse_ai_json(batch_raw)
                    
                    print(f"--- 首批生成 {len(test_cases)} 条用例 ---") # DEBUG
                    
                    batch_context = {
                        "path": path,
                        "method": method_upper,
                        "details_json": details_json,
                        "all_case_names": all_case_names,
                        "next_index": len(test_cases)
                    }
                    
                    return {
                        "total": total,
                        "test_cases": test_cases,
                        "generated_count": len(test_cases),
                        "batch_context": batch_context
                    }
                
                except Exception as e:
                    print(f"--- 生成测试用例过程中发生错误: {e} ---") # DEBUG
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=f"生成测试用例失败: {e}")
            
            break

        return {"message": "OpenAPI 规范中未找到可处理的接口", "test_cases": [], "total": 0, "generated_count": 0}
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- generate_test_cases_api 函数发生通用错误: {e} ---") # DEBUG
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成测试用例时发生未知错误: {e}")

@router.post("/generate_test_cases/batch")
async def generate_test_cases_batch_api(request: Request):
    print("--- generate_test_cases_batch_api 函数开始执行 ---") # DEBUG
    try:
        body = await request.json()
        batch_context = body.get("batch_context", {})
        
        path = batch_context["path"]
        method = batch_context["method"]
        details_json = batch_context["details_json"]
        all_case_names = batch_context["all_case_names"]
        next_index = batch_context["next_index"]
        
        end_index = min(next_index + BATCH_SIZE, len(all_case_names))
        batch_names = all_case_names[next_index:end_index]
        cases_names_str = "\n".join(f"- {name}" for name in batch_names)
        
        batch_prompt = BATCH_PROMPT_TEMPLATE.format(path=path, method=method, details_json=details_json, cases_names=cases_names_str)
        batch_messages = [
            {"role": "system", "content": "你是一个专业的测试工程师。请只返回 JSON 数组格式，不要包含任何额外解释或 Markdown 标记。"},
            {"role": "user", "content": batch_prompt}
        ]
        batch_raw = await call_deepseek_api(batch_messages)
        test_cases = _parse_ai_json(batch_raw)
        
        print(f"--- 批次生成 {len(test_cases)} 条用例，进度 {end_index}/{len(all_case_names)} ---") # DEBUG
        
        new_context = {
            "path": path,
            "method": method,
            "details_json": details_json,
            "all_case_names": all_case_names,
            "next_index": end_index
        }
        done = end_index >= len(all_case_names)
        
        return {
            "test_cases": test_cases,
            "generated_count": end_index,
            "total": len(all_case_names),
            "batch_context": new_context,
            "done": done
        }
    except Exception as e:
        print(f"--- 分批生成过程中发生错误: {e} ---") # DEBUG
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"分批生成测试用例失败: {e}")

def _normalize_assertions(assertions):
    if not isinstance(assertions, list):
        return []
    result = []
    for a in assertions:
        if isinstance(a, str):
            parts = a.strip().split(None, 2)
            if len(parts) >= 3:
                result.append({"check": parts[0], "comparator": parts[1], "expect": parts[2]})
            elif len(parts) == 2:
                result.append({"check": parts[0], "comparator": parts[1], "expect": ""})
            else:
                result.append({"check": a.strip(), "comparator": "json_equals", "expect": ""})
        elif isinstance(a, dict):
            if "type" in a and "value" in a:
                result.append({"check": a["type"], "comparator": a.get("operator", a.get("comparator", "json_equals")), "expect": a["value"]})
            elif "check" in a:
                result.append(a)
            else:
                result.append(a)
        else:
            result.append({"check": str(a), "comparator": "json_equals", "expect": ""})
    return result

def _ensure_dict_or_none(val):
    if val is None or isinstance(val, dict):
        return val
    return None

@router.post("/generate_test_cases/import")
async def import_generated_test_cases(request: Request, db: Session = Depends(get_db)):
    print("--- import_generated_test_cases 函数开始执行 ---") # DEBUG
    try:
        body = await request.json()
        cases = body.get("test_cases", [])
        module_id = body.get("module_id")
        if not cases:
            raise HTTPException(status_code=400, detail="没有要导入的测试用例")
        created = []
        for case in cases:
            tc_data = TestCaseCreate(
                name=case.get("name", ""),
                description=case.get("description"),
                url=case.get("url", ""),
                method=case.get("method", "GET"),
                content_type=case.get("content_type", "json"),
                headers=_ensure_dict_or_none(case.get("headers")),
                body=_ensure_dict_or_none(case.get("body")),
                extract_rules=_ensure_dict_or_none(case.get("extract_rules")),
                assertions=_normalize_assertions(case.get("assertions")),
                module_id=module_id,
            )
            db_case = crud_test_case.create_test_case(db, tc_data)
            created.append({"id": db_case.id, "name": db_case.name})
        print(f"--- 成功导入 {len(created)} 条测试用例 ---") # DEBUG
        return {"created_count": len(created), "created": created}
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- 导入测试用例过程中发生错误: {e} ---") # DEBUG
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"导入测试用例失败: {e}")