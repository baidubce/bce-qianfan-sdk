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

from qianfan.consts import DefaultValue
from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResourceV1,
)
from qianfan.resources.typing import JsonBody, QfLLMInfo, QfResponse


class Reranker(BaseResourceV1):
    """
    QianFan Reranker is an agent for calling QianFan reranker API.
    """

    def _local_models(self) -> Dict[str, QfLLMInfo]:
        info_list = {
            "bce-reranker-base_v1": QfLLMInfo(
                endpoint="/reranker/bce_reranker_base",
                required_keys={"_query", "documents"},
                optional_keys={"top_n"},
                input_price_per_1k_tokens=0.002,
            ),
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="",
                required_keys={"_query", "documents"},
                optional_keys={"top_n"},
            ),
        }
        # 获取最新的模型列表
        return self._merge_local_models_with_latest(info_list)

    @classmethod
    def api_type(cls) -> str:
        return "reranker"

    @classmethod
    def _default_model(cls) -> str:
        """
        default model of Reranker

        Args:
            None

        Returns:
           ""

        """
        return "bce-reranker-base_v1"

    def _generate_body(
        self, model: Optional[str], stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        Reranker needs to transform body (`_query` -> `query`)
        """
        body = super()._generate_body(model, stream, **kwargs)
        # "query" is conflict with QfRequest.query in params, so "_query" is
        # the argument in SDK so we need to change "_query" back to "query" here
        body["query"] = body["_query"]
        del body["_query"]
        return body

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert endpoint to Reranker API endpoint
        """
        return f"/reranker/{endpoint}"

    def do(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        **kwargs: Any,
    ) -> QfResponse:
        """
        Rerank the input documents according to the query.

        Parameters:
          query (str):
            User input for choosing the documents .
          documents (List[str]):
            The documents to be ranked.
          top_n (Optional[int]):
            The number of documents to be returned.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used.
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          retry_count (int):
            The number of times to retry the request in case of failure.
          request_timeout (float):
            The maximum time (in seconds) to wait for a response from the model.
          backoff_factor (float):
            A factor to increase the waiting time between retry attempts.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        please refer to the API documentation. The additional parameters can be passed
        as follows:

        ```
        Reranker().do(query=..., documents=[..], top_n=5)
        ```

        """
        kwargs["_query"] = query
        kwargs["documents"] = documents
        if top_n is not None:
            kwargs["top_n"] = top_n
        resp = self._do(
            model,
            retry_count=retry_count,
            request_timeout=request_timeout,
            backoff_factor=backoff_factor,
            endpoint=endpoint,
            **kwargs,
        )
        assert isinstance(resp, QfResponse)
        return resp

    async def ado(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        **kwargs: Any,
    ) -> QfResponse:
        """
        Rerank the input documents according to the query.

        Parameters:
          query str:
            User input for choosing the documents .
          documents (List[str]):
            The documents to be ranked.
          top_n (Optional[int]):
            The number of documents to be returned.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used.
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          retry_count (int):
            The number of times to retry the request in case of failure.
          request_timeout (float):
            The maximum time (in seconds) to wait for a response from the model.
          backoff_factor (float):
            A factor to increase the waiting time between retry attempts.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        please refer to the API documentation. The additional parameters can be passed
        as follows:

        ```
        Reranker().do(query=..., documents=[..], top_n=5)
        ```

        """
        kwargs["_query"] = query
        kwargs["documents"] = documents
        if top_n is not None:
            kwargs["top_n"] = top_n
        resp = await self._ado(
            model,
            retry_count=retry_count,
            request_timeout=request_timeout,
            backoff_factor=backoff_factor,
            endpoint=endpoint,
            **kwargs,
        )

        assert isinstance(resp, QfResponse)
        return resp
