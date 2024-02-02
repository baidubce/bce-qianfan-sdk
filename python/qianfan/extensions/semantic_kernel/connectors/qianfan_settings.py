# Copyright (c) 2023 Baidu, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any, Dict, List, Optional

from pydantic import Field
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


class QianfanEmbeddingRequestSettings(AIRequestSettings):
    ai_model_id: Optional[str] = Field(None, serialization_alias="model")
    texts: Optional[List[str]] = None
