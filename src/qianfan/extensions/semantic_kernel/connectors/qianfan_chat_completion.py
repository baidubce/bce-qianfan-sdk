# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any, List, Optional, Tuple, Union

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated


from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.google_palm.gp_request_settings import (
    GooglePalmChatRequestSettings,
    GooglePalmRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class QianfanChatCompletion(
    ChatCompletionClientBase, TextCompletionClientBase, AIServiceClientBase
):
    def __init__(
        self,
        model: Optional[str],
        endpoint: Optional[str],
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
        )

    async def complete_chat_async(
        self,
        messages: List[Tuple[str, str]],
        settings: GooglePalmRequestSettings,
    ) -> Union[str, List[str]]:
        settings.messages = messages
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_chat_request(settings)

        if settings.candidate_count > 1:
            return [
                (
                    candidate["output"]
                    if candidate["output"] is not None
                    else "I don't know."
                )
                for candidate in response.candidates
            ]
        if response.last is None:
            return "I don't know."  # PaLM returns None if it doesn't know
        return response.last

    async def complete_chat_stream_async(
        self,
        messages: List[Tuple[str, str]],
        settings: GooglePalmRequestSettings,
    ):
        raise NotImplementedError(
            "Google Palm API does not currently support streaming"
        )

    async def complete_async(
        self,
        prompt: str,
        settings: GooglePalmRequestSettings,
        **kwargs,
    ) -> Union[str, List[str]]:
        if kwargs.get("logger"):
            logger.warning(
                "The `logger` parameter is deprecated. Please use the `logging` module"
                " instead."
            )
        settings.messages = [("user", prompt)]
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_chat_request(settings)

        if settings.candidate_count > 1:
            return [
                (
                    candidate["output"]
                    if candidate["output"] is not None
                    else "I don't know."
                )
                for candidate in response.candidates
            ]
        if response.last is None:
            return "I don't know."  # PaLM returns None if it doesn't know
        return response.last

    async def complete_stream_async(
        self,
        prompt: str,
        settings: GooglePalmRequestSettings,
        **kwargs,
    ):
        if kwargs.get("logger"):
            logger.warning(
                "The `logger` parameter is deprecated. Please use the `logging` module"
                " instead."
            )
        raise NotImplementedError(
            "Google Palm API does not currently support streaming"
        )

    async def _send_chat_request(
        self,
        settings: GooglePalmRequestSettings,
    ):
        """
        Completes the given user message. If len(messages) > 1, and a
        conversation has not been initiated yet, it is assumed that chat history
        is needed for context. All messages preceding the last message will be
        utilized for context. This also enables Google PaLM to utilize memory
        and skills, which should be stored in the messages parameter as system
        messages.

        Arguments:
            messages {str} -- The message (from a user) to respond to.
            settings {GooglePalmRequestSettings} -- The request settings.
            context {str} -- Text that should be provided to the model first,
            to ground the response. If a system message is provided, it will be
            used as context.
            examples {ExamplesOptions} -- 	Examples of what the model should
            generate. This includes both the user input and the response that
            the model should emulate. These examples are treated identically to
            conversation messages except that they take precedence over the
            history in messages: If the total input size exceeds the model's
            input_token_limit the input will be truncated. Items will be dropped
            from messages before examples
            See: https://developers.generativeai.google/api/python/google/generativeai/types/ExampleOptions
            prompt {MessagePromptOptions} -- 	You may pass a
            types.MessagePromptOptions instead of a setting context/examples/messages,
            but not both.
            See: https://developers.generativeai.google/api/python/google/generativeai/types/MessagePromptOptions

        Returns:
            str -- The completed text.
        """
        if settings is None:
            raise ValueError("The request settings cannot be `None`")

        if settings.messages[-1][0] != "user":
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "The last message must be from the user",
            )
        try:
            palm.configure(api_key=self.api_key)
        except Exception as ex:
            raise PermissionError(
                "Google PaLM service failed to configure. Invalid API key provided.",
                ex,
            )
        if (
            self._message_history is None and settings.context is None
        ):  # If the conversation hasn't started yet and no context is provided
            context = ""
            if len(settings.messages) > 1:  # Check if we need context from messages
                for index, (role, message) in enumerate(settings.messages):
                    if index < len(settings.messages) - 1:
                        if role == "system":
                            context += message + "\n"
                        else:
                            context += role + ": " + message + "\n"
        try:
            if self._message_history is None:
                response = palm.chat(
                    **settings.prepare_settings_dict()
                )  # Start a new conversation
            else:
                response = self._message_history.reply(  # Continue the conversation
                    settings.messages[-1][1],
                )
            self._message_history = response  # Store response object for future use
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "Google PaLM service failed to complete the prompt",
                ex,
            )
        return response

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return GooglePalmChatRequestSettings
