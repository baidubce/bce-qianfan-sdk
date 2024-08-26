# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
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

from typing import Any, Optional

from qianfan import resources
from qianfan.config import Config, get_config
from qianfan.consts import DefaultValue
from qianfan.resources import ChatCompletion


class Qianfan:
    completions: resources.ChatCompletion
    chat: "Chat"
    embeddings: resources.Embedding
    config: Config

    def __init__(
        self,
        *,
        iam_access_key: Optional[str] = None,
        iam_secret_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        app_id: Optional[str] = None,
        base_url: Optional[str] = None,
        console_base_url: Optional[str] = None,
        request_timeout: Optional[int] = None,
        retry_count: int = DefaultValue.RetryCount,
        **kwargs: Any,
    ) -> None:
        # super().__init__(**kwargs)

        self.config = Config(
            ACCESS_KEY=iam_access_key or get_config().ACCESS_KEY,
            SECRET_KEY=iam_secret_key or get_config().SECRET_KEY,
            BEARER_TOKEN=bearer_token or get_config().BEARER_TOKEN,
            APP_ID=app_id or get_config().APP_ID,
            BASE_URL=base_url or get_config().BASE_URL,
            CONSOLE_API_BASE_URL=console_base_url or get_config().CONSOLE_API_BASE_URL,
            LLM_API_RETRY_COUNT=retry_count or get_config().LLM_API_RETRY_COUNT,
            LLM_API_RETRY_TIMEOUT=request_timeout or get_config().LLM_API_RETRY_TIMEOUT,
        )
        self.chat = Chat(client=self)


class Chat:
    _client: Qianfan

    def __init__(self, client: "Qianfan") -> None:
        self._client = client

    @property
    def completions(self) -> ChatCompletion:
        return ChatCompletion(config=self._client.config)
