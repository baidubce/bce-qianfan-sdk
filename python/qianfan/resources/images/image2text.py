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
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Tuple, Union

from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResourceV1,
    BatchRequestFuture,
)
from qianfan.resources.typing import QfLLMInfo, QfResponse


class Image2Text(BaseResourceV1):
    """
    QianFan Image2Text API Resource

    """

    def _self_supported_models(self) -> Dict[str, QfLLMInfo]:
        info_list = {
            "Fuyu-8B": QfLLMInfo(
                endpoint="/image2text/fuyu_8b",
                required_keys={"prompt", "image"},
                optional_keys={
                    "negative_prompt",
                    "size",
                    "n",
                    "steps",
                    "sampler_index",
                    "user_id",
                    "seed",
                    "cfg_scale",
                    "style",
                },
                input_price_per_1k_tokens=0.002,
            ),
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="",
                # the key of api is "query", which is conflict with query in params
                # use "prompt" to substitute
                required_keys={"prompt", "image"},
                optional_keys={
                    "user_id",
                },
            ),
        }
        # 获取最新的模型列表
        return self._merge_local_models_with_latest(info_list)

    @classmethod
    def api_type(cls) -> str:
        return "image2text"

    @classmethod
    def _default_model(self) -> str:
        """
        no default model for image2text

        Args:
            None

        Returns:
           "UNSPECIFIED_MODEL"

        """
        return UNSPECIFIED_MODEL

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert endpoint to image2text API endpoint
        """
        return f"/image2text/{endpoint}"

    def do(
        self,
        prompt: str,
        image: str,
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
        Execute a image2text action on the provided input prompt and generate responses.

        Parameters:
          prompt (str):
            The user input or prompt for which a response is generated.
          image (str):
            The user input base64 encoded image data for which a response is generated.
          model (Optional[str]):
            The name or identifier of the language model to use.
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          stream (bool):
            Whether to stream responses or not.
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
        Image2Text(endpoint="").do(prompt="", image="", xxx=vvv)
        ```

        """
        kwargs["prompt"] = prompt
        kwargs["image"] = image
        if request_id is not None:
            kwargs["request_id"] = request_id

        resp = self._do(
            model,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            endpoint=endpoint,
            **kwargs,
        )
        return resp

    async def ado(
        self,
        prompt: str,
        image: str,
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
        Async execute a image2text action on the provided input prompt and generate
        responses.

        Parameters:
          prompt (str):
            The user input or prompt for which a response is generated.
          image (str):
            The user input base64 encoded image data for which a response is generated.
          model (Optional[str]):
            The name or identifier of the language model to use.
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          stream (bool):
            Whether to stream responses or not.
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
        Image2Text(endpoint="").ado(prompt="", image="", xx=vv)
        ```

        """
        kwargs["prompt"] = prompt
        kwargs["image"] = image
        if request_id is not None:
            kwargs["request_id"] = request_id

        resp = await self._ado(
            model,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            endpoint=endpoint,
            **kwargs,
        )
        return resp

    def batch_do(
        self,
        input_list: List[Tuple[str, str]],
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> BatchRequestFuture:
        """
        Batch generate execute a image2text action on the provided inputs and
        generate responses.

        Parameters:
          input_list (Tuple(str, str)):
            The list user input prompt and base64 encoded image data for which a
            response is generated.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
          kwargs (Any):
            Please refer to `Plugin.do` for other parameters such as `model`,
            `endpoint`, `retry_count`, etc.

        ```
        response_list = Image2Text(endpoint="").batch_do([("...", "..."),
            ("...", "...")], worker_num = 10)
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
            partial(self.do, prompt=input[0], image=input[1], **kwargs)
            for input in input_list
        ]

        return self._batch_request(task_list, worker_num)

    async def abatch_do(
        self,
        input_list: List[Tuple[str, str]],
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Union[QfResponse, AsyncIterator[QfResponse]]]:
        """
        Async batch generate execute a image2text action on the provided inputs and
        generate responses.

        Parameters:
          input_list (Tuple(str, str)):
            The list user input prompt and base64 encoded image data for which a
            response is generated.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
          kwargs (Any):
            Please refer to `Plugin.ado` for other parameters such as `model`,
            `endpoint`, `retry_count`, etc.

        ```
        response_list = await Image2Text(endpoint="").abatch_do([("...", "..."),
            ("...", "...")], worker_num = 10)
        for response in response_list:
            # response is `QfResponse` if succeed, or response will be exception
            print(response)
        ```

        """
        tasks = [
            self.ado(prompt=input[0], image=input[1], **kwargs) for input in input_list
        ]
        return await self._abatch_request(tasks, worker_num)
