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

from functools import partial
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union

import qianfan.errors as errors
from qianfan.consts import DefaultValue
from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResource,
    BatchRequestFuture,
)
from qianfan.resources.typing import JsonBody, QfLLMInfo, QfMessages, QfResponse


class Plugin(BaseResource):
    """
    QianFan Plugin API Resource

    """

    def __init__(
        self, model: str = "EBPlugin", endpoint: Optional[str] = None, **kwargs: Any
    ) -> None:
        """
        Init for Plugins including
        Qianfan plugin: endpoint must be specified.
        EB plugin: plugins params must be specified.
        """
        if endpoint is None:
            # 转换成一言插件
            super().__init__(model, **kwargs)
        else:
            super().__init__(endpoint=endpoint, **kwargs)

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
            "EBPlugin": QfLLMInfo(
                # 一言插件 v1
                endpoint="/erniebot/plugins",
                required_keys={"messages", "plugins"},
                optional_keys={"user_id", "extra_data"},
            ),
            "EBPluginV2": QfLLMInfo(
                # 一言插件 v2
                endpoint="/erniebot/plugin",
                required_keys={"messages", "plugins"},
                optional_keys={"user_id", "extra_data"},
            ),
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="",
                # the key of api is "query", which is conflict with query in params
                # use "prompt" to substitute
                required_keys={"_query"},
                optional_keys={
                    "user_id",
                },
            ),
        }

    @classmethod
    def _default_model(self) -> str:
        """
        default model of Plugin is  `EBPlugin`

        Args:
            None

        Returns:
           "EBPlugin"

        """
        return "EBPlugin"

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert endpoint to ChatCompletion API endpoint
        """
        if endpoint != "":
            # 千帆插件
            return f"/plugin/{endpoint}/"
        else:
            # 一言插件
            if model not in self._supported_models():
                model = self._default_model()
            model_info = self._supported_models().get(model)
            assert model_info is not None
            return model_info.endpoint

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
        Plugin needs to transform body (`_query` -> `query`)
        """
        if model is None:
            body = super()._generate_body(model, endpoint, stream, **kwargs)
            # "query" is conflict with QfRequest.query in params, so "_query" is
            # the argument in SDK so we need to change "_query" back to "query" here
            body["query"] = body["_query"]
            del body["_query"]
            return body
        else:
            return super()._generate_body(model, endpoint, stream, **kwargs)

    def do(
        self,
        query: Union[str, QfMessages, List[Dict]],
        plugins: Optional[List[str]] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        Execute a plugin action on the provided input prompt and generate responses.

        Parameters:
          query Union[str, QfMessages, List[Dict]]:
            The user input for which a response is generated.
            Concretely, the following types are supported:
              query should be str for qianfan plugin, while
              query should be either QfMessages or list for EBPlugin
          plugins (Optional[List[str]]):
            A list of plugins to be used.
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
        if isinstance(query, str):
            kwargs["_query"] = query
            if request_id is not None:
                kwargs["request_id"] = request_id
        elif isinstance(query, list):
            kwargs["messages"] = query
        elif isinstance(query, QfMessages):
            kwargs["messages"] = query._to_list()
        else:
            raise errors.InvalidArgumentError(f"invalid query type {type(query)}")
        if plugins:
            kwargs["plugins"] = plugins
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
        query: Union[str, QfMessages, List[Dict]],
        plugins: Optional[List[str]] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        Async execute a plugin action on the provided input prompt and generate
        responses.

        Parameters:
          query Union[str, QfMessages, List[Dict]]:
            The user input for which a response is generated.
            Concretely, the following types are supported:
              query should be str for qianfan plugin, while
              query should be either QfMessages or list for EBPlugin
          plugins (Optional[List[str]]):
            A list of plugins to be used.
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
        if isinstance(query, str):
            kwargs["_query"] = query
            if request_id is not None:
                kwargs["request_id"] = request_id
        elif isinstance(query, list):
            kwargs["messages"] = query
        elif isinstance(query, QfMessages):
            kwargs["messages"] = query._to_list()
        else:
            raise errors.InvalidArgumentError(f"invalid query type {type(query)}")
        if plugins:
            kwargs["plugins"] = plugins

        return await self._ado(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            **kwargs,
        )

    def batch_do(
        self,
        query_list: List[Union[str, QfMessages, List[Dict]]],
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> BatchRequestFuture:
        """
        Batch generate execute a plugin action on the provided input prompt and
        generate responses.

        Parameters:
          query_list List[Union[str, QfMessages, List[Dict]]]:
            The list user input messages or prompt for which a response is generated.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
          kwargs (Any):
            Please refer to `Plugin.do` for other parameters such as `model`,
            `endpoint`, `retry_count`, etc.

        ```
        response_list = Plugin().batch_do(["...", "..."], worker_num = 10)
        for response in response_list:
            # return QfResponse if succeed, or exception will be raised
            print(response.result())
        # or
        while response_list.finished_count() != response_list.task_count():
            time.sleep(1)
        print(response_list.results())
        ```

        """
        task_list = [partial(self.do, query=query, **kwargs) for query in query_list]

        return self._batch_request(task_list, worker_num)

    async def abatch_do(
        self,
        query_list: List[Union[str, QfMessages, List[Dict]]],
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Union[QfResponse, AsyncIterator[QfResponse]]]:
        """
        Async batch execute a plugin action on the provided input prompt and generate
        responses.

        Parameters:
          query_list List[Union[str, QfMessages, List[Dict]]]:
            The list user input messages or prompt for which a response is generated.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
          kwargs (Any):
            Please refer to `Plugin.ado` for other parameters such as `model`,
            `endpoint`, `retry_count`, etc.

        ```
        response_list = await Plugin().abatch_do([...], worker_num = 10)
        for response in response_list:
            # response is `QfResponse` if succeed, or response will be exception
            print(response)
        ```

        """
        tasks = [self.ado(query, **kwargs) for query in query_list]
        return await self._abatch_request(tasks, worker_num)
