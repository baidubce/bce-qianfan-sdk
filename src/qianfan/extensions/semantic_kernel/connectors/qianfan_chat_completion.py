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
from typing import Any, AsyncIterator, Dict, List, Optional

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

from qianfan import QfResponse
from qianfan.extensions.semantic_kernel.connectors.qianfan_settings import (
    QianfanChatRequestSettings,
    QianfanRequestSettings,
    QianfanTextRequestSettings,
)
from qianfan.resources import ChatCompletion


class QianfanChatCompletion(
    ChatCompletionClientBase, TextCompletionClientBase, AIServiceClientBase
):
    client: Any
    """
    qianfan sdk client
    """

    def __init__(
        self,
        model: str = "ERNIE-Bot-turbo",
        endpoint: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initializes a new instance of the QianfanChatCompletion class.

        Arguments:
            model Optional[str]
                model name for qianfan.
            endpoint Optional[str]
                model endpoint for qianfan.
            **kwargs: Any
                additional arguments to pass to the init qianfan client
        """
        super().__init__(
            ai_model_id=model,
            client=ChatCompletion(
                model=model,
                endpoint=endpoint,
                **kwargs,
            ),
        )

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        settings: QianfanRequestSettings,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Complete a chat with the given messages.

        Args:
            messages (List[Dict[str, str]]):
                chat messages history and query
            settings (QianfanRequestSettings):
                chat query settings, including hype parameters,
                configurations for client
            kwargs: Any
                additional arguments to pass to the qianfan client
        Returns:
            Optional[str]: response message content
        """
        assert isinstance(settings, QianfanChatRequestSettings)
        settings.messages = messages
        response = await self._send_chat_request(settings, **kwargs)
        assert isinstance(response, QfResponse)
        return response["result"]

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        settings: QianfanRequestSettings,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion with the given messages.

        Args:
            messages (List[Dict[str, str]]):
                chat messages history and query
            settings (QianfanRequestSettings):
                chat query settings, including hype parameters,
                configurations for client
            kwargs: Any
                additional arguments to pass to the qianfan client

        Yields:
            str: streaming response message content
        """
        assert isinstance(settings, QianfanChatRequestSettings)
        settings.messages = messages
        settings.stream = True
        response = await self._send_chat_request(settings, **kwargs)
        assert isinstance(response, AsyncIterator)
        async for r in response:
            yield r["result"]

    async def complete_async(
        self,
        prompt: str,
        settings: QianfanRequestSettings,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Complete a chat with a given prompt.

        Args:
            prompt (str):
                prompt to completion
            settings (QianfanRequestSettings):
                chat query settings, including hype parameters,
                configurations for client

        Raises:
            ValueError: invalid input or settings

        Returns:
            Optional[str]:
                completion response message content
        """
        if not isinstance(settings, QianfanChatRequestSettings) and not isinstance(
            settings, QianfanTextRequestSettings
        ):
            raise ValueError(
                "settings must be QianfanChatRequestSettings or"
                " QianfanTextRequestSettings"
            )
        settings = QianfanChatRequestSettings(
            **settings.model_dump(),
        )
        if not settings.messages:
            settings.messages = []
        settings.messages.append({"role": "user", "content": prompt})
        response = await self._send_chat_request(settings, **kwargs)
        assert isinstance(response, QfResponse)
        return response["result"]

    async def complete_stream_async(
        self,
        prompt: str,
        settings: QianfanRequestSettings,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream completion with the given prompt.

        Args:
            prompt (str):
                prompt to completion
            settings (QianfanRequestSettings):
                completion query settings, including hype parameters,
                configurations for client
            kwargs: Any
                additional arguments to pass to the qianfan client

        Yields:
            str: streaming response message content
        """
        if not isinstance(settings, QianfanChatRequestSettings) and not isinstance(
            settings, QianfanTextRequestSettings
        ):
            raise ValueError(
                "settings must be QianfanChatRequestSettings or"
                " QianfanTextRequestSettings"
            )
        settings = QianfanChatRequestSettings(
            **settings.model_dump(),
        )
        if not settings.messages:
            settings.messages = []
        settings.messages.append({"role": "user", "content": prompt})
        settings.stream = True
        res = await self._send_chat_request(settings, **kwargs)
        assert isinstance(res, AsyncIterator)
        async for r in res:
            yield r["result"]

    async def _send_chat_request(
        self, settings: QianfanChatRequestSettings, **kwargs: Any
    ) -> Optional[QfResponse]:
        """
        Send chat request to the qianfan client.

        Args:
            settings (QianfanChatRequestSettings):
                settings object for chat/completion request

        Returns:
            Optional[QfResponse]:
                response object from the qianfan client
        """
        try:
            data = {**settings.prepare_settings_dict(), **kwargs}
            response = await self.client.ado(**data)
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "qianfan chat service failed to response the messages",
                ex,
            )

        return response

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return QianfanChatRequestSettings
