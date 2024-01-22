import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from numpy import array, ndarray
from qianfan.extensions.semantic_kernel.connectors.qianfan_settings import (
    QianfanEmbeddingRequestSettings,
    QianfanRequestSettings,
)
from qianfan.resources import Embedding
from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)

logger: logging.Logger = logging.getLogger(__name__)


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
        Initializes a new instance of the QianfanChatCompletion class.

        Arguments:
            model Optional[str]
                model name for qianfan.
            endpoint Optional[str]
                model endpoint for qianfan.
            app_ak_sk: Optional[Tuple[str, str]], see
                https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Dlkm79mnx#access_token%E9%80%82%E7%94%A8%E7%9A%84api
            iam_ak_sk: Optional[Tuple[str, str]], see
                https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Dlkm79mnx#%E5%AE%89%E5%85%A8%E8%AE%A4%E8%AF%81aksk%E7%AD%BE%E5%90%8D%E8%AE%A1%E7%AE%97%E9%80%82%E7%94%A8%E7%9A%84api
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
        batch_size: Optional[int] = None,
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
        settings = QianfanEmbeddingRequestSettings(
            **kwargs,
        )
        raw_embeddings = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]  # noqa: E203
            settings.texts = batch
            raw_embedding = await self._send_embedding_request(
                settings=settings,
            )
            raw_embeddings.extend(raw_embedding)
        return array(raw_embeddings)

    async def _send_embedding_request(
        self, settings: QianfanRequestSettings, **kwargs: Any
    ) -> Union[Union[str, None], AsyncIterator[Union[str, None]]]:
        if settings is None:
            raise ValueError("The request settings cannot be `None`")
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
        return QianfanEmbeddingRequestSettings
