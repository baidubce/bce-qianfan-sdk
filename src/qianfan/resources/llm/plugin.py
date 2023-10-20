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

from typing import Any, AsyncIterator, Dict, Iterator, Optional, Union

import qianfan.errors as errors
from qianfan.resources.llm.base import UNSPECIFIED_MODEL, BaseResource
from qianfan.resources.typing import JsonBody, QfLLMInfo, QfResponse


class Plugin(BaseResource):
    """
    QianFan Plugin API Resource

    """

    def __init__(
        self, model: Optional[str] = None, endpoint: Optional[str] = None, **kwargs: Any
    ) -> None:
        """
        Init for Plugin
        `model` will not be accepted
        """
        if model is not None:
            raise errors.InvalidArgumentError("`model` is not supported for plugin")
        super().__init__(model, endpoint, **kwargs)

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
        """
        Only one endpoint provide for plugins

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        return {
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="",
                # the key of api is "query", which is conflict with query in params
                # use "prompt" to substitute
                required_keys={"prompt"},
                optional_keys={
                    "user_id",
                },
            ),
        }

    @classmethod
    def _default_model(self) -> str:
        """
        default model of ChatCompletion `ERNIE-Bot-turbo`

        Args:
            None

        Returns:
           "ERNIE-Bot-turbo"

        """
        return UNSPECIFIED_MODEL

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert endpoint to ChatCompletion API endpoint
        """
        return f"/plugin/{endpoint}/"

    def _check_params(
        self,
        model: Optional[str],
        endpoint: Optional[str],
        stream: bool,
        retry_count: int,
        request_timeout: float,
        backoff_factor: float,
        **kwargs: Any,
    ) -> None:
        """
        check params
        plugin does not support model and endpoint arguments
        """
        if model is not None:
            raise errors.InvalidArgumentError("model is not supported in plugin")
        return super()._check_params(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            **kwargs,
        )

    def _generate_body(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        Plugin needs to transform body (`prompt` -> `query`)
        """
        if endpoint == "":
            raise errors.ArgumentNotFoundError("`endpoint` must be provided")
        body = super()._generate_body(model, endpoint, stream, **kwargs)
        # "query" is conflict with query in params, so "prompt" is the argument in SDK
        # so we need to change "prompt" back to "query" here
        body["query"] = body["prompt"]
        del body["prompt"]
        return body

    def do(
        self,
        prompt: str,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = 1,
        request_timeout: float = 60,
        backoff_factor: float = 0,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        Execute a plugin action on the provided input prompt and generate responses.

        Parameters:
          prompt (str):
            The user input or prompt for which a response is generated.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used(ERNIE-Bot-turbo).
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          stream (bool):
            If set to True, the responses are streamed back as an iterator. If False, a
            single response is returned.
          retry_count (int):
            The number of times to retry the request in case of failure.
          request_timeout (float):
            The maximum time (in seconds) to wait for a response from the model.
          backoff_factor (float):
            A factor to increase the waiting time between retry attempts.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Additional parameters like `temperature` will vary depending on the model,
        please refer to the API documentation. The additional parameters can be passed
        as follows:

        ```
        Plugin().do(prompt = ..., temperature = 0.2, top_p = 0.5)
        ```

        """
        kwargs["prompt"] = prompt

        return self._do(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            **kwargs,
        )

    async def ado(
        self,
        prompt: str,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = 1,
        request_timeout: float = 60,
        backoff_factor: float = 0,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        Async execute a plugin action on the provided input prompt and generate
        responses.

        Parameters:
          prompt (str):
            The user input or prompt for which a response is generated.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used(ERNIE-Bot-turbo).
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          stream (bool):
            If set to True, the responses are streamed back as an iterator. If False, a
            single response is returned.
          retry_count (int):
            The number of times to retry the request in case of failure.
          request_timeout (float):
            The maximum time (in seconds) to wait for a response from the model.
          backoff_factor (float):
            A factor to increase the waiting time between retry attempts.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Additional parameters like `temperature` will vary depending on the model,
        please refer to the API documentation. The additional parameters can be passed
        as follows:

        ```
        Plugin().do(prompt = ..., temperature = 0.2, top_p = 0.5)
        ```

        """
        kwargs["prompt"] = prompt

        return await self._ado(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            **kwargs,
        )
