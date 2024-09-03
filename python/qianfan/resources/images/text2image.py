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

import base64
from functools import partial
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union

from qianfan.consts import DefaultLLMModel
from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResourceV1,
    BatchRequestFuture,
)
from qianfan.resources.typing import QfLLMInfo, QfResponse


class Text2Image(BaseResourceV1):
    """
    QianFan Text2Image API Resource

    """

    def _self_supported_models(self) -> Dict[str, QfLLMInfo]:
        """
        models provide for text2image

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        info_list = {
            "Stable-Diffusion-XL": QfLLMInfo(
                endpoint="/text2image/sd_xl",
                required_keys={"prompt"},
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
            ),
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
        # 获取最新的模型列表
        return self._merge_local_models_with_latest(info_list)

    @classmethod
    def api_type(cls) -> str:
        return "text2image"

    @classmethod
    def _default_model(self) -> str:
        """
        default model of text2image `Stable-Diffusion-XL`

        Args:
            None

        Returns:
           "Stable-Diffusion-XL"

        """
        return DefaultLLMModel.Text2Image

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert endpoint to text2image API endpoint
        """
        return f"/text2image/{endpoint}"

    def do(
        self,
        prompt: str,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        with_decode: Optional[str] = None,
        retry_count: int = 1,
        request_timeout: float = 60,
        request_id: Optional[str] = None,
        backoff_factor: float = 0,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        Execute a text2image action on the provided input prompt and generate responses.

        Parameters:
          prompt (str):
            The user input or prompt for which a response is generated.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used(Stable-Diffusion-XL).
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          with_decode(Optional[str]):
            The way to decode data. If not provided, the decode is not used.
            use "base64" to auto decode from data.
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
        Text2Image().do(prompt = ..., steps=20)
        ```

        """
        kwargs["prompt"] = prompt
        if request_id is not None:
            kwargs["request_id"] = request_id

        resp = self._do(
            model,
            False,
            retry_count,
            request_timeout,
            backoff_factor,
            endpoint=endpoint,
            **kwargs,
        )
        assert isinstance(resp, QfResponse)
        if with_decode == "base64":
            for i in resp["body"]["data"]:
                i["image"] = base64.b64decode(i["b64_image"])
        return resp

    async def ado(
        self,
        prompt: str,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        with_decode: Optional[str] = None,
        retry_count: int = 1,
        request_timeout: float = 60,
        request_id: Optional[str] = None,
        backoff_factor: float = 0,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        Async execute a text2image action on the provided input prompt and generate
        responses.

        Parameters:
          prompt (str):
            The user input or prompt for which a response is generated.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used(Stable-Diffusion-XL).
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          with_decode(Optional[str]):
            The way to decode data. If not provided, the decode is not used.
            use "base64" to auto decode from data.
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
        Text2Image().do(prompt = ..., steps=20)
        ```

        """
        kwargs["prompt"] = prompt
        if request_id is not None:
            kwargs["request_id"] = request_id

        resp = await self._ado(
            model,
            False,
            retry_count,
            request_timeout,
            backoff_factor,
            endpoint=endpoint,
            **kwargs,
        )
        assert isinstance(resp, QfResponse)
        if with_decode == "base64":
            for i in resp["body"]["data"]:
                i["image"] = base64.b64decode(i["b64_image"])
        return resp

    def batch_do(
        self,
        prompt_list: List[str],
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> BatchRequestFuture:
        """
        Batch generate execute a text2image action on the provided input prompt and
        generate responses.

        Parameters:
          prompt_list (List[str]):
            The list user input or prompt for which a response is generated.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
          kwargs (Any):
            Please refer to `Text2Image.do` for other parameters such as `model`,
            `endpoint`, `retry_count`, etc.

        ```
        response_list = Text2Image().batch_do(["...", "..."], worker_num = 10)
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
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Union[QfResponse, AsyncIterator[QfResponse]]]:
        """
        Async batch execute a text2image action on the provided input prompt and
        generate responses.

        Parameters:
          prompt_list (List[str]):
            The list user input or prompt for which a response is generated.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
          kwargs (Any):
            Please refer to `Text2Image.ado` for other parameters such as `model`,
            `endpoint`, `retry_count`, etc.

        ```
        response_list = await Text2Image().abatch_do([...], worker_num = 10)
        for response in response_list:
            # response is `QfResponse` if succeed, or response will be exception
            print(response)
        ```

        """
        tasks = [self.ado(prompt=prompt, **kwargs) for prompt in prompt_list]
        return await self._abatch_request(tasks, worker_num)
