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
from datetime import datetime, timezone
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
    Type,
    Union,
)

import qianfan.errors as errors
from qianfan import get_config
from qianfan.consts import APIErrorCode, Consts, DefaultValue
from qianfan.resources.console.service import Service
from qianfan.resources.requestor.openapi_requestor import (
    QfAPIV2Requestor,
    create_api_requestor,
)
from qianfan.resources.typing import (
    JsonBody,
    Literal,
    QfLLMInfo,
    QfResponse,
    RetryConfig,
)
from qianfan.utils import log_info, log_warn, utils
from qianfan.utils.cache.base import KvCache
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
        max_workers = (
            worker_num if worker_num else min(len(tasks) + 1, MAX_WORKER_THREAD_COUNT)
        )

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

    def get_future_list(self) -> List[Future]:
        return self._future_list

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


class VersionBase(object):
    def __init__(
        self, version: Optional[Literal["1", "2", 1, 2]] = None, **kwargs: Any
    ) -> None:
        self._version = str(version) if version else "1"
        self._real = self._real_base(self._version)(**kwargs)
        self._backup = self._real_base("1")(**kwargs)

    @classmethod
    def _real_base(cls, version: str) -> Type[BaseResource]:
        """
        return the real base class
        """
        raise NotImplementedError

    def access_token(self) -> str:
        """
        get access token
        """
        return self._real.access_token()

    def models(self) -> Set[str]:
        return self._real.models()

    def get_model_info(self, model: str) -> QfLLMInfo:
        """
        Get the model info of `model`

        Args:
            model (str): the name of the model,

        Return:
            Information of the model
        """

        return self._real.get_model_info(model)

    def _need_downgrade(self) -> bool:
        """
        check if the model need to be downgrade
        """
        return get_config().V2_INFER_API_DOWNGRADE and self._version != "1"

    def _do(self, **kwargs: Any) -> Union[QfResponse, Iterator[QfResponse]]:
        if self._need_downgrade():
            return self._do_downgrade(**kwargs)
        # assert self._real has function `do`
        return self._real.do(**kwargs)  # type: ignore

    async def _ado(self, **kwargs: Any) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        if self._need_downgrade():
            return await self._ado_downgrade(**kwargs)
        # assert self._real has function `ado`
        return await self._real.ado(**kwargs)  # type: ignore

    def _do_downgrade(self, **kwargs: Any) -> Union[QfResponse, Iterator[QfResponse]]:
        resp = self._backup.do(**kwargs)  # type: ignore
        if "stream" not in kwargs or kwargs["stream"] is False:
            return self._convert_v2_response_to_v1(resp)

        return self._convert_v2_response_to_v1_stream(resp)

    async def _ado_downgrade(
        self, **kwargs: Any
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        resp = await self._backup.ado(**kwargs)  # type: ignore
        if "stream" not in kwargs or kwargs["stream"] is False:
            return self._convert_v2_response_to_v1(resp)

        return self._convert_v2_response_to_v1_async_stream(resp)

    def _convert_v2_request_to_v1(self, request: Any) -> Any:
        return request

    def _convert_v2_response_to_v1(self, response: QfResponse) -> QfResponse:
        return response

    def _convert_v2_response_to_v1_stream(
        self, iterator: Iterator[QfResponse]
    ) -> Iterator[QfResponse]:
        for i in iterator:
            yield i

    async def _convert_v2_response_to_v1_async_stream(
        self, iterator: AsyncIterator[QfResponse]
    ) -> AsyncIterator[QfResponse]:
        async for i in iterator:
            yield i


class BaseResource(object):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        pass

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
        raise NotImplementedError

    @classmethod
    def update_with_cache_model_infos(cls) -> Dict[str, Dict[str, QfLLMInfo]]:
        """
        update the model info with cache and return `_runtime_models_info`

        Returns:
            Dict[str, Dict[str, QfLLMInfo]]: model infos list
        """
        global _last_update_time
        global _runtime_models_info
        global _model_infos_access_lock
        if _last_update_time.timestamp() == 0:
            # 首次加载本地缓存
            cache = KvCache()
            value = cache.get(key=Consts.QianfanLLMModelsListCacheKey)
            if value is not None:
                try:
                    with _model_infos_access_lock:
                        _last_update_time = value.get(
                            "update_time",
                            datetime(1970, 1, 1, second=1, tzinfo=timezone.utc),
                        )

                        _runtime_models_info = cls._merge_models(
                            _runtime_models_info, value.get("models", {})
                        )
                except TypeError:
                    # 防止value格式不对齐可能产生的问题
                    # global_disk_cache.delete(Consts.QianfanLLMModelsListCacheKey)
                    ...
            else:
                with _model_infos_access_lock:
                    _last_update_time = datetime(
                        1970, 1, 1, second=1, tzinfo=timezone.utc
                    )
        return _runtime_models_info

    @staticmethod
    def _merge_models(
        merged: Dict[str, Dict[str, QfLLMInfo]],
        new: Dict[str, Dict[str, QfLLMInfo]],
    ) -> Dict[str, Dict[str, QfLLMInfo]]:
        for model_type, list in new.items():
            if model_type not in merged:
                merged[model_type] = {}
            merged[model_type] = {**merged[model_type], **list}

        return merged

    @staticmethod
    def format_model_infos_cache(
        type_model_list: Dict[str, Dict[str, QfLLMInfo]], update_time: datetime
    ) -> Any:
        """
        format the model info to cache format
        Args:
            model_list (Dict[str, QfLLMInfo]): model infos list
            expired_time (float): expire time of the cache
        Returns:
            a dict which key is preset model and value is the endpoint
        """
        return {"models": type_model_list, "update_time": update_time}

    def _generate_header(
        self, model: Optional[str], stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate header
        """
        kwargs = copy.deepcopy(kwargs)
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"][Consts.XRequestID] = (
            kwargs["request_id"]
            if kwargs.get("request_id")
            else (
                f"{Consts.QianfanRequestIdDefaultPrefix}-{utils.generate_letter_num_random_id(16)}"
            )
        )
        return kwargs["headers"]

    def _generate_query(
        self, model: Optional[str], stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate query
        """
        if "query" in kwargs:
            return kwargs["query"]
        return {}

    def _generate_body(
        self, model: Optional[str], stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate body
        """
        kwargs = copy.deepcopy(kwargs)
        IGNORED_KEYS = {"headers", "query", "request_id"}
        for key in IGNORED_KEYS:
            if key in kwargs:
                del kwargs[key]

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

    @classmethod
    def models(cls) -> Set[str]:
        """
        get all supported model names
        """
        raise NotImplementedError

    @classmethod
    def api_type(cls) -> str:
        raise NotImplementedError

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

    def access_token(self) -> str:
        """
        get access token
        """
        raise NotImplementedError

    def generate_retry_config(
        self,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        retry_jitter: float = DefaultValue.RetryJitter,
        retry_err_codes: Set[int] = DefaultValue.RetryErrCodes,
        retry_max_wait_interval: float = DefaultValue.RetryMaxWaitInterval,
    ) -> RetryConfig:
        """
        generate retry config
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

        retry_config = RetryConfig(
            retry_count=retry_count,
            timeout=request_timeout,
            backoff_factor=backoff_factor,
            jitter=retry_jitter,
            retry_err_codes=retry_err_codes,
            max_wait_interval=retry_max_wait_interval,
        )
        return retry_config

    def _do(
        self,
        model: Optional[str] = None,
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
        retry_config = self.generate_retry_config(
            retry_count=retry_count,
            request_timeout=request_timeout,
            backoff_factor=backoff_factor,
            retry_jitter=retry_jitter,
            retry_err_codes=retry_err_codes,
            retry_max_wait_interval=retry_max_wait_interval,
        )

        return self._request(model, stream, retry_config, **kwargs)

    async def _ado(
        self,
        model: Optional[str] = None,
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
        qianfan resource basic do

        Args:
            **kwargs (dict): kv dict data。

        """
        retry_config = self.generate_retry_config(
            retry_count=retry_count,
            request_timeout=request_timeout,
            backoff_factor=backoff_factor,
            retry_jitter=retry_jitter,
            retry_err_codes=retry_err_codes,
            retry_max_wait_interval=retry_max_wait_interval,
        )

        return await self._arequest(model, stream, retry_config, **kwargs)

    def _request(
        self,
        model: Optional[str],
        stream: bool,
        retry_config: RetryConfig,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        raise NotImplementedError

    async def _arequest(
        self,
        model: Optional[str],
        stream: bool,
        retry_config: RetryConfig,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        raise NotImplementedError


class BaseResourceV1(BaseResource):
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
            model_info = self.get_model_info(model_name)
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

    def _request(
        self,
        model: Optional[str],
        stream: bool,
        retry_config: RetryConfig,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        qianfan resource basic do

        Args:
            **kwargs (dict): kv dict data。

        """
        endpoint = self._extract_endpoint(**kwargs)

        model, endpoint = self._update_model_and_endpoint(model, endpoint)

        endpoint = self._get_endpoint_from_dict(model, endpoint, stream)
        refreshed_model_list: bool = False
        kwargs["endpoint"] = endpoint
        while True:
            try:
                resp = self._client.llm(
                    endpoint=endpoint,
                    header=self._generate_header(model, stream, **kwargs),
                    query=self._generate_query(model, stream, **kwargs),
                    body=self._generate_body(model, stream, **kwargs),
                    stream=stream,
                    data_postprocess=self._data_postprocess,
                    retry_config=retry_config,
                )
            except errors.APIError as e:
                if (
                    e.error_code == APIErrorCode.UnsupportedMethod
                    and not refreshed_model_list
                ):
                    list = get_latest_supported_models(True)
                    endpoint = list.get(self.api_type(), {}).get(model)
                    refreshed_model_list = True
                    continue
                else:
                    raise e
            break

        return resp

    async def _arequest(
        self,
        model: Optional[str],
        stream: bool,
        retry_config: RetryConfig,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        endpoint = self._extract_endpoint(**kwargs)
        model, endpoint = self._update_model_and_endpoint(model, endpoint)

        endpoint = self._get_endpoint_from_dict(model, endpoint, stream)
        refreshed_model_list: bool = False
        kwargs["endpoint"] = endpoint
        while True:
            try:
                resp = await self._client.async_llm(
                    endpoint=endpoint,
                    header=self._generate_header(model, stream, **kwargs),
                    query=self._generate_query(model, stream, **kwargs),
                    body=self._generate_body(model, stream, **kwargs),
                    stream=stream,
                    data_postprocess=self._data_postprocess,
                    retry_config=retry_config,
                )
            except errors.APIError as e:
                if (
                    e.error_code == APIErrorCode.UnsupportedMethod
                    and not refreshed_model_list
                ):
                    list = get_latest_supported_models(True)
                    endpoint = list.get(self.api_type(), {}).get(model)
                    refreshed_model_list = True
                    continue
                else:
                    raise e
            break
        return resp

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
        """
        get preset model list

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        return get_latest_supported_models().get(cls.api_type(), {})

    @classmethod
    def api_type(cls) -> str:
        return "chat"

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
        try:
            model_info = self.get_model_info(model)
        except errors.InvalidArgumentError:
            if self._endpoint is not None:
                return QfLLMInfo(endpoint=self._endpoint)
            else:
                raise
        return model_info

    def _get_endpoint_from_dict(
        self, model: Optional[str], endpoint: Optional[str], stream: bool
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

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert user-provided endpoint to real endpoint
        """
        raise NotImplementedError

    def access_token(self) -> str:
        """
        get access token
        """
        return self._client._auth.access_token()

    def _generate_body(
        self, model: str | None, stream: bool, **kwargs: Any
    ) -> Dict[str, Any]:
        endpoint = self._extract_endpoint(**kwargs)
        if "endpoint" in kwargs:
            kwargs.pop("endpoint")
        body = super()._generate_body(model, stream, **kwargs)
        model_info: Optional[QfLLMInfo] = None
        if model is not None:
            try:
                model_info = self.get_model_info(model)
                # warn if user provide unexpected arguments
                for key in kwargs:
                    if (
                        len(model_info.required_keys) > 0
                        and key not in model_info.required_keys
                    ) and (
                        len(model_info.optional_keys) > 0
                        and key not in model_info.optional_keys
                    ):
                        log_warn(
                            f"This key `{key}` does not seem to be a parameter that the"
                            f" model `{model}` will accept"
                        )
            except errors.InvalidArgumentError:
                ...

        if model_info is None:
            # 使用默认模型
            try:
                default_model_info = self.get_model_info(self._default_model())
                if default_model_info.endpoint == endpoint:
                    model_info = default_model_info
            except errors.InvalidArgumentError:
                ...

        # 非默认模型
        if model_info is None:
            model_info = self._supported_models()[UNSPECIFIED_MODEL]
        for key in model_info.required_keys:
            if key not in kwargs:
                raise errors.ArgumentNotFoundError(
                    f"The required key `{key}` is not provided."
                )
        return body

    @classmethod
    def _extract_endpoint(cls, **kwargs: Any) -> str:
        """
        extract endpoint from kwargs
        """
        return kwargs.get("endpoint", None)

    @classmethod
    def models(cls) -> Set[str]:
        """
        get all supported model names
        """
        ...
        models = set(cls._supported_models().keys())
        models.remove(UNSPECIFIED_MODEL)
        return models

    @classmethod
    def get_model_info(cls, model: str) -> QfLLMInfo:
        """
        Get the model info of `model`

        Args:
            model (str): the name of the model,

        Return:
            Information of the model
        """
        # try update with local cache
        cls.update_with_cache_model_infos()
        # get the supported_models list
        model_info_list = {k.lower(): v for k, v in cls._supported_models().items()}
        model_info = model_info_list.get(model.lower())
        if model_info is None:
            use_iam_aksk_msg = ""
            if get_config().ACCESS_KEY is None or get_config().SECRET_KEY is None:
                use_iam_aksk_msg = (
                    "might use `QIANFAN_ACCESS_KEY` and `QIANFAN_SECRET_KEY` instead to"
                    " get complete features supported."
                )
            raise errors.InvalidArgumentError(
                f"The provided model `{model}` is not in the list of supported models."
                " If this is a recently added model, try using the `endpoint`"
                " arguments and create an issue to tell us. Supported models:"
                f" {cls.models()} {use_iam_aksk_msg}"
            )
        return model_info


class BaseResourceV2(BaseResource):
    def __init__(self, model: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._model = model
        self._client = QfAPIV2Requestor(**kwargs)

    def _request(
        self,
        model: Optional[str],
        stream: bool,
        retry_config: RetryConfig,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        qianfan resource basic do

        Args:
            **kwargs (dict): kv dict data。

        """

        resp = self._client.llm(
            endpoint=self._api_path(),
            header=self._generate_header(model, stream, **kwargs),
            query=self._generate_query(model, stream, **kwargs),
            body=self._generate_body(model, stream, **kwargs),
            stream=stream,
            retry_config=retry_config,
        )

        return resp

    async def _arequest(
        self,
        model: Optional[str],
        stream: bool,
        retry_config: RetryConfig,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        resp = await self._client.async_llm(
            endpoint=self._api_path(),
            header=self._generate_header(model, stream, **kwargs),
            query=self._generate_query(model, stream, **kwargs),
            body=self._generate_body(model, stream, **kwargs),
            stream=stream,
            retry_config=retry_config,
        )

        return resp

    def _generate_body(
        self, model: str | None, stream: bool, **kwargs: Any
    ) -> Dict[str, Any]:
        body = super()._generate_body(model, stream, **kwargs)
        if model is not None:
            body["model"] = model
        elif self._model is not None:
            body["model"] = self._model
        else:
            body["model"] = self._default_model()
        return body

    @classmethod
    def _default_model(cls) -> str:
        raise NotImplementedError

    def _api_path(self) -> str:
        raise NotImplementedError


# {api_type: {model_name: QfLLMInfo}}
_runtime_models_info = {}  # type: ignore
_last_update_time = datetime(1970, 1, 1, tzinfo=timezone.utc)  # type: ignore
_model_infos_access_lock = threading.Lock()  # type: ignore


def trim_prefix(s: str, prefix: str) -> str:
    if s.startswith(prefix):
        return s[len(prefix) :]
    else:
        return s


def get_latest_supported_models(
    refresh_focus: bool = False,
    update_interval: Optional[float] = None,
) -> Dict[str, Dict[str, QfLLMInfo]]:
    """
    fetch supported models from server if `_last_update_time` is expired
    and update the `_runtime_models_info`
    """
    if get_config().ACCESS_KEY is None or get_config().SECRET_KEY is None:
        return {}

    if get_config().ENABLE_PRIVATE:
        # 私有化直接跳过
        return {}

    global _last_update_time
    global _runtime_models_info
    if update_interval is None:
        update_interval = get_config().ACCESS_TOKEN_REFRESH_MIN_INTERVAL
    if (
        datetime.now(timezone.utc) - _last_update_time
    ).total_seconds() >= update_interval or refresh_focus:
        _model_infos_access_lock.acquire()
        if (
            datetime.now(timezone.utc) - _last_update_time
        ).total_seconds() < update_interval and not refresh_focus:
            _model_infos_access_lock.release()
            return _runtime_models_info
        try:
            svc_list = Service.list()["result"]["common"]
        except Exception as e:
            log_warn(f"fetch_supported_models failed: {e}")
            _model_infos_access_lock.release()
            _last_update_time = datetime.now(timezone.utc)
            return _runtime_models_info

        # get preset services:
        for s in svc_list:
            [api_type, model_endpoint] = trim_prefix(
                s["url"],
                "{}{}/".format(
                    DefaultValue.BaseURL,
                    Consts.ModelAPIPrefix,
                ),
            ).split("/")
            model_info = _runtime_models_info.get(api_type)
            if model_info is None:
                model_info = {}
            model_info[s["name"]] = QfLLMInfo(
                endpoint="/{}/{}".format(api_type, model_endpoint),
                api_type=api_type,
            )
            _runtime_models_info[api_type] = model_info
            _last_update_time = datetime.now(timezone.utc)
        cache = KvCache()
        cache.set(
            key=Consts.QianfanLLMModelsListCacheKey,
            value=BaseResource.format_model_infos_cache(
                _runtime_models_info, _last_update_time
            ),
        )
        _model_infos_access_lock.release()
    return _runtime_models_info
