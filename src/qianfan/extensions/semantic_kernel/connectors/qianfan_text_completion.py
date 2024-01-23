import logging
from typing import Any, AsyncIterator, Optional, Union

from qianfan.extensions.semantic_kernel.connectors.qianfan_settings import (
    QianfanRequestSettings,
    QianfanTextRequestSettings,
)
from qianfan.resources import Completion
from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class QianfanTextCompletion(TextCompletionClientBase, AIServiceClientBase):
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
        Initializes a new instance of the QianfanCompletion class.

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
            client=Completion(
                model=model,
                endpoint=endpoint,
                **kwargs,
            ),
        )

    async def complete_async(
        self,
        prompt: str,
        settings: QianfanRequestSettings,
        **kwargs,
    ) -> Union[str, None]:
        if isinstance(settings, QianfanTextRequestSettings):
            settings.prompt = prompt
        else:
            raise ValueError("The request settings must be QianfanTextRequestSettings")
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_completion_request(settings)

        return response["result"]

    async def complete_stream_async(
        self,
        prompt: str,
        settings: QianfanRequestSettings,
        **kwargs,
    ) -> AsyncIterator[Union[str, None]]:
        if isinstance(settings, QianfanTextRequestSettings):
            settings.prompt = prompt
        else:
            settings.messages = [{"role": "user", "content": prompt}]
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        settings.stream = True
        response = await self._send_completion_request(settings)

        return response

    async def _send_completion_request(
        self, settings: QianfanRequestSettings, **kwargs: Any
    ) -> Union[Union[str, None], AsyncIterator[Union[str, None]]]:
        if settings is None:
            raise ValueError("The request settings cannot be `None`")
        try:
            data = {**settings.prepare_settings_dict(), **kwargs}
            print("data: ", data)
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
        return QianfanTextRequestSettings
