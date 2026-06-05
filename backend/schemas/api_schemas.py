# backend/schemas/api_schemas.py
from pydantic import BaseModel
from typing import Dict, Any

class OpenApiSpecInput(BaseModel):
    """用于接收 OpenAPI/Swagger 规范 JSON 内容的 Pydantic 模型。"""
    openapi_spec: Dict[str, Any]