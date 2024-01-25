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

from numpy import array, ndarray
from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)

from qianfan.extensions.semantic_kernel.connectors.qianfan_settings import (
    QianfanEmbeddingRequestSettings,
    QianfanRequestSettings,
)
from qianfan.resources import Embedding


class QianfanTextEmbedding(EmbeddingGeneratorBase, AIServiceClientBase):
    client: Any
    """
    qianfan sdk client
    """

    def __init__(
        self,
        model: str = "Embedding-V1",
        endpoint: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initializes a new instance of the QianfanTextEmbedding class.

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
            client=Embedding(
                model=model,
                endpoint=endpoint,
                **kwargs,
            ),
        )

    async def generate_embeddings_async(
        self,
        texts: List[str],
        batch_size: int = 16,
        **kwargs: Dict[str, Any],
    ) -> ndarray:
        """Generates embeddings for the given texts.

        Arguments:
            texts {List[str]} -- The texts to generate embeddings for.
            kwargs {Dict[str, Any]} -- Additional arguments to pass to the request,
                see QianfanEmbeddingRequestSettings for the details.

        Returns:
            ndarray -- The embeddings for the text.

        """
        settings = QianfanEmbeddingRequestSettings()
        raw_embeddings: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]  # noqa: E203
            settings.texts = batch
            raw_embedding = await self._send_embedding_request(
                settings=settings, **kwargs
            )
            raw_embeddings.extend(raw_embedding)
        return array(raw_embeddings)

    async def _send_embedding_request(
        self, settings: QianfanRequestSettings, **kwargs: Any
    ) -> List[List[float]]:
        """
        Send embeddings request to the qianfan client.

        Args:
            settings (QianfanRequestSettings):
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
                "qianfan embedding service failed to response the messages",
                ex,
            )
        return [r["embedding"] for r in response["data"]]

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return QianfanEmbeddingRequestSettings
