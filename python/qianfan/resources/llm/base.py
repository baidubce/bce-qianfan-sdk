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

from __future__ import annotations

import asyncio
import concurrent.futures
import copy
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Coroutine,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import qianfan.errors as errors
from qianfan import get_config
from qianfan.consts import Consts, DefaultValue
from qianfan.resources.requestor.openapi_requestor import create_api_requestor
from qianfan.resources.typing import JsonBody, QfLLMInfo, QfResponse, RetryConfig
from qianfan.utils import log_info, log_warn, utils
from qianfan.version import VERSION

# This is used when user provides `endpoint`
# In such cases, SDK cannot know which model the user is using
# This constant is used to express no model is spcified,
# so that SDK still can get the requirements of API from _supported_models()
UNSPECIFIED_MODEL = "UNSPECIFIED_MODEL"
MAX_WORKER_THREAD_COUNT = 1000


class BatchRequestFuture(object):
    """
    Future object for batch request
    """

    def __init__(
        self,
        tasks: Sequence[Callable[[], Union[QfResponse, Iterator[QfResponse]]]],
        worker_num: Optional[int] = None,
    ) -> None:
        """
        Init batch request future
        """
        max_workers = worker_num if worker_num else len(tasks) + 1
        if max_workers > MAX_WORKER_THREAD_COUNT:
            max_workers = MAX_WORKER_THREAD_COUNT

        self._future_list: List[Future[Union[QfResponse, Iterator[QfResponse]]]] = []
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._finished_count = 0
        self._task_count = len(tasks)
        self._lock = threading.Lock()
        for task in tasks:
            future = self._executor.submit(task)
            future.add_done_callback(self._future_callback)
            self._future_list.append(future)

    def _future_callback(
        self, fn: Future[Union[QfResponse, Iterator[QfResponse]]]
    ) -> None:
        """
        callback when one task is finished
        """
        with self._lock:
            self._finished_count += 1
            if self._finished_count == self._task_count:
                log_info("All tasks finished, exeutor will be shutdown")
                self._executor.shutdown(wait=False)

    def wait(self) -> None:
        """
        Wait for all tasks to be finished
        """
        concurrent.futures.wait(self._future_list)

    def results(self) -> List[Union[QfResponse, Iterator[QfResponse], Exception]]:
        """
        Wait for all tasks to be finished, and return the results.
        The order of the elements in the output is the same as the order
        of the elements in the input.
        """
        res_list: List[Union[QfResponse, Iterator[QfResponse], Exception]] = []
        for future in self._future_list:
            try:
                res = future.result()
                res_list.append(res)
            except Exception as e:
                res_list.append(e)
        return res_list

    def task_count(self) -> int:
        """
        Return the total count of tasks
        """
        return len(self._future_list)

    def finished_count(self) -> int:
        """
        Return the number of tasks that have been finished
        """
        with self._lock:
            return self._finished_count

    def __iter__(self) -> Iterator[Future[Union[QfResponse, Iterator[QfResponse]]]]:
        """
        Return the iterator of the future list.
        Use `result()` to get the result of each task.

        ```
        for item in batch_request_future:
            print(item.result())
        ```
        """
        return self._future_list.__iter__()

    def __len__(self) -> int:
        """
        return the number of tasks
        """
        return len(self._future_list)


class BaseResource(object):
    """
    base class of Qianfan object
    """

    def __init__(
        self,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        init resource
        """
        self._model = model
        self._endpoint = endpoint
        self._client = create_api_requestor(**kwargs)

    def _update_model_and_endpoint(
        self, model: Optional[str], endpoint: Optional[str]
    ) -> Tuple[Optional[str], str]:
        """
        update model and endpoint from constructor
        """
        # if user do not provide new model and endpoint,
        # use the model and endpoint from constructor
        if model is None and endpoint is None:
            model = self._model
            endpoint = self._endpoint
        if endpoint is None:
            model_name = self._default_model() if model is None else model
            model_info = self._supported_models().get(model_name, None)
            if model_info is None:
                raise errors.InvalidArgumentError(
                    f"The provided model `{model}` is not in the list of supported"
                    " models. If this is a recently added model, try using the"
                    " `endpoint` arguments and create an issue to tell us. Supported"
                    f" models: {self.models()}"
                )
            endpoint = model_info.endpoint
        else:
            endpoint = self._convert_endpoint(model, endpoint)
        return model, endpoint

    def _do(
        self,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        retry_jitter: float = DefaultValue.RetryJitter,
        retry_err_codes: Set[int] = DefaultValue.RetryErrCodes,
        retry_max_wait_interval: float = DefaultValue.RetryMaxWaitInterval,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        qianfan resource basic do

        Args:
            **kwargs (dict): kv dict data。

        """
        config = get_config()
        if (
            retry_count == DefaultValue.RetryCount
            and config.LLM_API_RETRY_COUNT != DefaultValue.RetryCount
        ):
            retry_count = config.LLM_API_RETRY_COUNT
        if (
            request_timeout == DefaultValue.RetryTimeout
            and config.LLM_API_RETRY_TIMEOUT != DefaultValue.RetryTimeout
        ):
            request_timeout = config.LLM_API_RETRY_TIMEOUT
        if (
            backoff_factor == DefaultValue.RetryBackoffFactor
            and config.LLM_API_RETRY_BACKOFF_FACTOR != DefaultValue.RetryBackoffFactor
        ):
            backoff_factor = config.LLM_API_RETRY_BACKOFF_FACTOR
        if (
            retry_jitter == DefaultValue.RetryJitter
            and config.LLM_API_RETRY_JITTER != DefaultValue.RetryJitter
        ):
            retry_jitter = config.LLM_API_RETRY_JITTER
        if (
            retry_err_codes == DefaultValue.RetryErrCodes
            and config.LLM_API_RETRY_ERR_CODES != DefaultValue.RetryErrCodes
        ):
            retry_err_codes = config.LLM_API_RETRY_ERR_CODES
        if (
            retry_max_wait_interval == DefaultValue.RetryMaxWaitInterval
            and config.LLM_API_RETRY_MAX_WAIT_INTERVAL
            != DefaultValue.RetryMaxWaitInterval
        ):
            retry_max_wait_interval = config.LLM_API_RETRY_MAX_WAIT_INTERVAL

        model, endpoint = self._update_model_and_endpoint(model, endpoint)
        self._check_params(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            **kwargs,
        )
        retry_config = RetryConfig(
            retry_count=retry_count,
            timeout=request_timeout,
            backoff_factor=backoff_factor,
            jitter=retry_jitter,
            retry_err_codes=retry_err_codes,
            max_wait_interval=retry_max_wait_interval,
        )
        endpoint = self._get_endpoint_from_dict(model, endpoint, stream, **kwargs)
        resp = self._client.llm(
            endpoint=endpoint,
            header=self._generate_header(model, endpoint, stream, **kwargs),
            query=self._generate_query(model, endpoint, stream, **kwargs),
            body=self._generate_body(model, endpoint, stream, **kwargs),
            stream=stream,
            data_postprocess=self._data_postprocess,
            retry_config=retry_config,
        )
        return resp

    async def _ado(
        self,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        retry_jitter: float = DefaultValue.RetryJitter,
        retry_err_codes: Set[int] = DefaultValue.RetryErrCodes,
        retry_max_wait_interval: float = DefaultValue.RetryMaxWaitInterval,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        qianfan aio resource basic do

        Args:
            **kwargs: kv dict data

        Returns:
            None

        """
        config = get_config()
        if (
            retry_count == DefaultValue.RetryCount
            and config.LLM_API_RETRY_COUNT != DefaultValue.RetryCount
        ):
            retry_count = config.LLM_API_RETRY_COUNT
        if (
            request_timeout == DefaultValue.RetryTimeout
            and config.LLM_API_RETRY_TIMEOUT != DefaultValue.RetryTimeout
        ):
            request_timeout = config.LLM_API_RETRY_TIMEOUT
        if (
            backoff_factor == DefaultValue.RetryBackoffFactor
            and config.LLM_API_RETRY_BACKOFF_FACTOR != DefaultValue.RetryBackoffFactor
        ):
            backoff_factor = config.LLM_API_RETRY_BACKOFF_FACTOR
        if (
            retry_jitter == DefaultValue.RetryJitter
            and config.LLM_API_RETRY_JITTER != DefaultValue.RetryJitter
        ):
            retry_jitter = config.LLM_API_RETRY_JITTER
        if (
            retry_err_codes == DefaultValue.RetryErrCodes
            and config.LLM_API_RETRY_ERR_CODES != DefaultValue.RetryErrCodes
        ):
            retry_err_codes = config.LLM_API_RETRY_ERR_CODES
        if (
            retry_max_wait_interval == DefaultValue.RetryMaxWaitInterval
            and config.LLM_API_RETRY_MAX_WAIT_INTERVAL
            != DefaultValue.RetryMaxWaitInterval
        ):
            retry_max_wait_interval = config.LLM_API_RETRY_MAX_WAIT_INTERVAL
        model, endpoint = self._update_model_and_endpoint(model, endpoint)
        self._check_params(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            **kwargs,
        )

        retry_config = RetryConfig(
            retry_count=retry_count,
            timeout=request_timeout,
            backoff_factor=backoff_factor,
            jitter=retry_jitter,
            retry_err_codes=retry_err_codes,
            max_wait_interval=retry_max_wait_interval,
        )
        endpoint = self._get_endpoint_from_dict(model, endpoint, stream, **kwargs)
        resp = await self._client.async_llm(
            endpoint=endpoint,
            header=self._generate_header(model, endpoint, stream, **kwargs),
            query=self._generate_query(model, endpoint, stream, **kwargs),
            body=self._generate_body(model, endpoint, stream, **kwargs),
            stream=stream,
            data_postprocess=self._data_postprocess,
            retry_config=retry_config,
        )
        return resp

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
        check user provide params
        """
        if stream is True and retry_count != 1:
            log_warn("retry is not available when stream is enabled")

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
        """
        preset model list

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        raise NotImplementedError

    @classmethod
    def _default_model(cls) -> str:
        """
        default model

        Args:
            None

        Return:
            a str which is the default model name
        """
        raise NotImplementedError

    @classmethod
    def get_model_info(cls, model: str) -> QfLLMInfo:
        """
        Get the model info of `model`

        Args:
            model (str): the name of the model,

        Return:
            Information of the model
        """
        model_info = cls._supported_models().get(model)
        if model_info is None:
            raise errors.InvalidArgumentError(
                f"The provided model `{model}` is not in the list of supported models."
                " If this is a recently added model, try using the `endpoint`"
                " arguments and create an issue to tell us. Supported models:"
                f" {cls.models()}"
            )
        return model_info

    def _get_endpoint(self, model: str) -> QfLLMInfo:
        """
        get the endpoint of the given `model`

        Args:
            model (str): the name of the model,
                         must be defined in self._supported_models()

        Returns:
            str: the endpoint of the input `model`

        Raises:
            QianfanError: if the input is not in self._supported_models()
        """
        if model not in self._supported_models():
            if self._endpoint is not None:
                return QfLLMInfo(endpoint=self._endpoint)
            raise errors.InvalidArgumentError(
                f"The provided model `{model}` is not in the list of supported models."
                " If this is a recently added model, try using the `endpoint`"
                " arguments and create an issue to tell us. Supported models:"
                f" {self.models()}"
            )
        return self._supported_models()[model]

    def _get_endpoint_from_dict(
        self, model: Optional[str], endpoint: Optional[str], stream: bool, **kwargs: Any
    ) -> str:
        """
        extract the endpoint of the model in kwargs, or use the endpoint defined in
        __init__

        Args:
            **kwargs (dict): any dict

        Returns:
            str: the endpoint of the model in kwargs

        """
        if endpoint is not None:
            return endpoint
        if model is not None:
            return self._get_endpoint(model).endpoint
        return self._get_endpoint(self._default_model()).endpoint

    def _generate_header(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate header
        """
        if "header" not in kwargs:
            kwargs["header"] = {}
        kwargs["header"][Consts.XRequestID] = (
            kwargs["request_id"]
            if "request_id" in kwargs
            else (
                f"{Consts.QianfanRequestIdDefaultPrefix}-"
                f"{utils.generate_letter_num_random_id(16)}"
            )
        )
        return kwargs["header"]

    def _generate_query(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate query
        """
        if "query" in kwargs:
            return kwargs["query"]
        return {}

    def _generate_body(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate body
        """
        kwargs = copy.deepcopy(kwargs)
        IGNORED_KEYS = {"headers", "query"}
        for key in IGNORED_KEYS:
            if key in kwargs:
                del kwargs[key]
        if model is not None and model in self._supported_models():
            model_info = self._supported_models()[model]
            # warn if user provide unexpected arguments
            for key in kwargs:
                if (
                    key not in model_info.required_keys
                    and key not in model_info.optional_keys
                ):
                    log_warn(
                        f"This key `{key}` does not seem to be a parameter that the"
                        f" model `{model}` will accept"
                    )
        else:
            default_model_info = self._supported_models()[self._default_model()]
            if endpoint == default_model_info.endpoint:
                model_info = default_model_info
            else:
                model_info = self._supported_models()[UNSPECIFIED_MODEL]

        for key in model_info.required_keys:
            if key not in kwargs:
                raise errors.ArgumentNotFoundError(
                    f"The required key `{key}` is not provided."
                )
        kwargs["stream"] = stream
        if "extra_parameters" not in kwargs:
            kwargs["extra_parameters"] = {}
        kwargs["extra_parameters"]["request_source"] = f"qianfan_py_sdk_v{VERSION}"
        return kwargs

    def _data_postprocess(self, data: QfResponse) -> QfResponse:
        """
        post process data after get request response
        """
        return data

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert user-provided endpoint to real endpoint
        """
        raise NotImplementedError

    @classmethod
    def models(cls) -> Set[str]:
        """
        get all supported model names
        """
        models = set(cls._supported_models().keys())
        models.remove(UNSPECIFIED_MODEL)
        return models

    def access_token(self) -> str:
        """
        get access token
        """
        return self._client._auth.access_token()

    def _batch_request(
        self,
        tasks: Sequence[Callable[[], Union[QfResponse, Iterator[QfResponse]]]],
        worker_num: Optional[int] = None,
    ) -> BatchRequestFuture:
        """
        create batch prediction task and return future
        """
        if worker_num is not None and worker_num <= 0:
            raise errors.InvalidArgumentError("worker_num must be greater than 0")
        return BatchRequestFuture(tasks, worker_num)

    async def _abatch_request(
        self,
        tasks: Sequence[
            Coroutine[Any, Any, Union[QfResponse, AsyncIterator[QfResponse]]]
        ],
        worker_num: Optional[int] = None,
    ) -> List[Union[QfResponse, AsyncIterator[QfResponse]]]:
        """
        async do batch prediction
        """
        if worker_num is not None and worker_num <= 0:
            raise errors.InvalidArgumentError("worker_num must be greater than 0")
        if worker_num:
            sem = asyncio.Semaphore(worker_num)
        else:
            sem = None

        async def _with_concurrency_limit(
            task: Coroutine[Any, Any, Union[QfResponse, AsyncIterator[QfResponse]]]
        ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
            if sem:
                async with sem:
                    return await task
            else:
                return await task

        return await asyncio.gather(
            *[asyncio.ensure_future(_with_concurrency_limit(task)) for task in tasks],
            return_exceptions=True,
        )
