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
from qianfan.consts import DefaultLLMModel, DefaultValue
from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResource,
    BatchRequestFuture,
)
from qianfan.resources.typing import JsonBody, QfLLMInfo, QfResponse


class Embedding(BaseResource):
    """
    QianFan Embedding is an agent for calling QianFan embedding API.
    """

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
        """
        preset model list of Embedding
        support model:
         - Embedding-V1
         - bge-large-en
         - bge-large-zh

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        return {
            "Embedding-V1": QfLLMInfo(
                endpoint="/embeddings/embedding-v1",
                required_keys={"input"},
                optional_keys={"user_id"},
            ),
            "bge-large-en": QfLLMInfo(
                endpoint="/embeddings/bge_large_en",
                required_keys={"input"},
                optional_keys={"user_id"},
            ),
            "bge-large-zh": QfLLMInfo(
                endpoint="/embeddings/bge_large_zh",
                required_keys={"input"},
                optional_keys={"user_id"},
            ),
            "tao-8k": QfLLMInfo(
                endpoint="/embeddings/tao_8k",
                required_keys={"input"},
                optional_keys={"user_id"},
            ),
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="", required_keys={"input"}, optional_keys=set()
            ),
        }

    @classmethod
    def _default_model(cls) -> str:
        """
        default model of Embedding `Embedding-V1`

        Args:
            None

        Returns:
           "Embedding-V1"

        """
        return DefaultLLMModel.Embedding

    def _generate_body(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        need to check whether stream is set in Embedding
        """
        if stream is True:
            raise errors.InvalidArgumentError("Stream is not supported for embedding")
        if "texts" not in kwargs:
            raise errors.ArgumentNotFoundError("input not found in kwargs")
        kwargs["input"] = kwargs["texts"]
        del kwargs["texts"]
        return super()._generate_body(model, endpoint, stream, **kwargs)

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert endpoint to Embedding API endpoint
        """
        return f"/embeddings/{endpoint}"

    def do(
        self,
        texts: List[str],
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
        Generate embeddings for a list of input texts using a specified model.

        Parameters:
          texts (List[str]):
            A list of input texts for which embeddings need to be generated.
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
        Embedding().do(texts = ..., temperature = 0.2, top_p = 0.5)
        ```

        """
        kwargs["texts"] = texts
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
        texts: List[str],
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
        Async generate embeddings for a list of input texts using a specified model.

        Parameters:
          texts (List[str]):
            A list of input texts for which embeddings need to be generated.
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
        Embedding().do(texts = ..., temperature = 0.2, top_p = 0.5)
        ```

        """
        kwargs["texts"] = texts
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
        texts_list: List[List[str]],
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> BatchRequestFuture:
        """
        Batch generate embeddings for a list of input texts using a specified model.

        Parameters:
          texts_list (List[List[str]]):
            List of the input text list to generate the embeddings.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
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
        task_list = [partial(self.do, texts=texts, **kwargs) for texts in texts_list]

        return self._batch_request(task_list, worker_num)

    async def abatch_do(
        self,
        texts_list: List[List[str]],
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Union[QfResponse, AsyncIterator[QfResponse]]]:
        """
        Async batch generate embeddings for a list of input texts using a specified
        model.

        Parameters:
          texts_list (List[List[str]]):
            List of the input text list to generate the embeddings.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
          kwargs (Any):
            Please refer to `Embedding.ado` for other parameters such as `model`,
            `endpoint`, `retry_count`, etc.

        ```
        response_list = await Embedding().abatch_do([...], worker_num = 10)
        for response in response_list:
            # response is `QfResponse` if succeed, or response will be exception
            print(response)
        ```

        """
        tasks = [self.ado(texts=texts, **kwargs) for texts in texts_list]
        return await self._abatch_request(tasks, worker_num)
