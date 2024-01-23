from typing import Any, Dict, List, Optional, Union

from pydantic import Field, model_validator
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class QianfanRequestSettings(AIRequestSettings):
    ai_model_id: Optional[str] = Field(None, serialization_alias="model")
    temperature: float = Field(0.95, g=0.0, le=1.0)
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stream: Optional[bool] = None
    retry_config: Optional[Any] = None


class QianfanTextRequestSettings(QianfanRequestSettings):
    prompt: Optional[str] = None


class QianfanChatRequestSettings(QianfanRequestSettings):
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    function_call: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = None


class QianfanEmbeddingRequestSettings(QianfanRequestSettings):
    texts: Optional[List[str]] = None
