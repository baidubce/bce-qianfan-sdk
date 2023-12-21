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
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
)

from qianfan.consts import DefaultLLMModel
from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResource,
    BatchRequestFuture,
)
from qianfan.resources.llm.chat_completion import ChatCompletion
from qianfan.resources.typing import JsonBody, QfLLMInfo, QfResponse


class Completion(BaseResource):
    """
    QianFan Completion is an agent for calling QianFan completion API.
    """

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
        """
        preset model list of Completions

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        return {
            "ERNIE-Bot-turbo": QfLLMInfo(
                endpoint="/chat/eb-instant",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                },
            ),
            "ERNIE-Bot": QfLLMInfo(
                endpoint="/chat/completions",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "max_output_tokens",
                },
            ),
            "ERNIE-Bot-4": QfLLMInfo(
                endpoint="/chat/completions_pro",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "max_output_tokens",
                },
            ),
            "ERNIE-Bot-8k": QfLLMInfo(
                endpoint="/chat/ernie_bot_8k",
                required_keys={"messages"},
                optional_keys={
                    "functions",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "stream",
                    "system",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "user_id",
                },
            ),
            "EB-turbo-AppBuilder": QfLLMInfo(
                endpoint="/chat/ai_apaas",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "system",
                    "user_id",
                },
            ),
            "BLOOMZ-7B": QfLLMInfo(
                endpoint="/chat/bloomz_7b1",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "Llama-2-7b-chat": QfLLMInfo(
                endpoint="/chat/llama_2_7b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "Llama-2-13b-chat": QfLLMInfo(
                endpoint="/chat/llama_2_13b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "Llama-2-70b-chat": QfLLMInfo(
                endpoint="/chat/llama_2_70b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "Qianfan-BLOOMZ-7B-compressed": QfLLMInfo(
                endpoint="/chat/qianfan_bloomz_7b_compressed",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "Qianfan-Chinese-Llama-2-7B": QfLLMInfo(
                endpoint="/chat/qianfan_chinese_llama_2_7b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "ChatGLM2-6B-32K": QfLLMInfo(
                endpoint="/chat/chatglm2_6b_32k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "AquilaChat-7B": QfLLMInfo(
                endpoint="/chat/aquilachat_7b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "XuanYuan-70B-Chat-4bit": QfLLMInfo(
                endpoint="/chat/xuanyuan_70b_chat",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "Qianfan-Chinese-Llama-2-13B": QfLLMInfo(
                endpoint="/chat/qianfan_chinese_llama_2_13b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "ChatLaw": QfLLMInfo(
                endpoint="/chat/chatlaw",
                required_keys={"messages", "extra_parameters"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_p",
                },
            ),
            "SQLCoder-7B": QfLLMInfo(
                endpoint="/completions/sqlcoder_7b",
                required_keys={"prompt"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            "CodeLlama-7b-Instruct": QfLLMInfo(
                endpoint="/completions/codellama_7b_instruct",
                required_keys={"prompt"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                },
            ),
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="",
                required_keys={"prompt"},
                optional_keys=set(),
            ),
        }

    @classmethod
    def _default_model(cls) -> str:
        """
        default model of Completion: ERNIE-Bot-turbo

        Args:
            None

        Returns:
           ERNIE-Bot-turbo

        """
        return DefaultLLMModel.Completion

    def _generate_body(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate body
        """
        if endpoint[1:].startswith("chat"):
            # is using chat to simulate completion
            kwargs["messages"] = [{"role": "user", "content": kwargs["prompt"]}]
            del kwargs["prompt"]
        body = super()._generate_body(model, endpoint, stream, **kwargs)

        return body

    def _data_postprocess(self, data: QfResponse) -> QfResponse:
        """
        to compat with completions api, when using chat completion to mock,
        the response needs to be modified
        """
        if data.body is not None:
            data.body["object"] = "completion"
        return super()._data_postprocess(data)

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert endpoint to Completion API endpoint
        """
        if model is not None and model in ChatCompletion._supported_models():
            return ChatCompletion()._convert_endpoint(model, endpoint)
        if endpoint in [
            info.endpoint for info in list(Completion._supported_models().values())
        ]:
            return endpoint
        return f"/completions/{endpoint}"

    def do(
        self,
        prompt: str,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = 1,
        request_timeout: float = 60,
        request_id: Optional[str] = None,
        backoff_factor: float = 0,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        Generate a completion based on the user-provided prompt.

        Parameters:
          prompt (str):
            The input prompt to generate the continuation from.
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
        Completion().do(prompt = ..., temperature = 0.2, top_p = 0.5)
        ```

        """
        kwargs["prompt"] = prompt
        if request_id is not None:
            kwargs["request_id"] = request_id

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
        request_id: Optional[str] = None,
        backoff_factor: float = 0,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        Async generate a completion based on the user-provided prompt.

        Parameters:
          prompt (str):
            The input prompt to generate the continuation from.
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
        Completion().do(prompt = ..., temperature = 0.2, top_p = 0.5)
        ```

        """
        kwargs["prompt"] = prompt
        if request_id is not None:
            kwargs["request_id"] = request_id

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
        prompt_list: List[str],
        worker_num: int = 1,
        **kwargs: Any,
    ) -> BatchRequestFuture:
        """
        Batch generate a completion based on the user-provided prompt.

        Parameters:
          prompt_list (List[str]):
            The input prompt list to generate the continuation from.
          worker_num (int):
            The number of prompts to process at the same time.
          kwargs (Any):
            Please refer to `Completion.do` for other parameters such as `model`,
            `endpoint`, `retry_count`, etc.

        ```
        response_list = Completion().batch_do(["...", "..."], worker_num = 10)
        for response in response_list:
            # return QfResponse if succeed, or exception will be raised
            print(response.result())
        # or
        while response_list.finished_count() != response_list.task_count():
            time.sleep(1)
        print(response_list.results())
        ```

        """
        task_list = [
            partial(self.do, prompt=prompt, **kwargs) for prompt in prompt_list
        ]

        return self._batch_request(task_list, worker_num)

    async def abatch_do(
        self,
        prompt_list: List[str],
        worker_num: int = 1,
        **kwargs: Any,
    ) -> List[Union[QfResponse, AsyncIterator[QfResponse]]]:
        """
        Async batch generate a completion based on the user-provided prompt.

        Parameters:
          prompt_list (List[str]):
            The input prompt list to generate the continuation from.
          worker_num (int):
            The number of prompts to process at the same time.
          kwargs (Any):
            Please refer to `Completion.ado` for other parameters such as `model`,
            `endpoint`, `retry_count`, etc.

        ```
        response_list = await Completion().abatch_do([...], worker_num = 10)
        for response in response_list:
            # response is `QfResponse` if succeed, or response will be exception
            print(response)
        ```

        """
        tasks = [self.ado(prompt=prompt, **kwargs) for prompt in prompt_list]
        return await self._abatch_request(tasks, worker_num)
