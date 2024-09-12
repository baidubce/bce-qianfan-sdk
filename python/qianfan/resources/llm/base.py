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
from qianfan import get_config, get_config_with_kwargs
from qianfan.config import Config
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
from qianfan.utils import log_debug, log_info, log_warn, utils
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
        self._real = self._real_base(self._version, **kwargs)(**kwargs)
        if self._version != "1":
            try:
                self._backup = self._real_base("1", **kwargs)(**kwargs)
            except Exception as e:
                log_debug(
                    f"Failed to create V1 backup instance, error: {e}, "
                    "will use the latest version instead."
                )

    @classmethod
    def _real_base(cls, version: str, **kwargs: Any) -> Type[BaseResource]:
        """
        return the real base class
        """
        raise NotImplementedError

    def access_token(self) -> str:
        """
        get access token
        """
        return self._real.access_token()

    @utils.class_or_instancemethod  # type: ignore
    def models(
        self_or_cls,
        version: Optional[Literal["1", "2", 1, 2]] = None,
    ) -> Set[str]:  # type ignore
        if version is not None:
            return self_or_cls._real_base(str(version)).models()
        if isinstance(self_or_cls, type):
            cls = self_or_cls
            return cls._real_base(version="1").models()
        self = self_or_cls
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
        return self._real.config.V2_INFER_API_DOWNGRADE and self._version != "1"

    def _do(self, **kwargs: Any) -> Union[QfResponse, Iterator[QfResponse]]:
        if self._need_downgrade() and self._backup:
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
    _runtime_models_info = {}  # type: ignore
    """
    动态模型列表
    """
    _last_update_time = datetime(1970, 1, 1, tzinfo=timezone.utc)  # type: ignore
    _model_infos_access_lock = threading.Lock()  # type: ignore

    def __init__(
        self,
        config: Optional[Config] = None,
        **kwargs: Any,
    ) -> None:
        if config is not None:
            self._config = config
            return

        if len(kwargs) != 0:
            self._config = get_config_with_kwargs(**kwargs)
        else:
            self._config = get_config()

    @property
    def config(self) -> Config:
        assert self._config is not None
        return self._config

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

    def get_model_info(self, model: str) -> QfLLMInfo:
        """
        Get the model info of `model`

        Args:
            model (str): the name of the model,

        Return:
            Information of the model
        """
        raise NotImplementedError

    def _init_model_info_with_cache(self) -> Dict[str, Dict[str, QfLLMInfo]]:
        """
        update the model info with local cache and return `_runtime_models_info`
        this function should be called only once for each resource instance

        Returns:
            Dict[str, Dict[str, QfLLMInfo]]: model infos list
        """
        with self._model_infos_access_lock:
            if self._last_update_time.timestamp() == 0:
                # 首次加载本地缓存
                cache = KvCache()
                value = cache.get(
                    key=f"{Consts.QianfanLLMModelsListCacheKey}_{self.config.auth_key()}"
                )
                if value is not None:
                    try:
                        self._last_update_time = value.get(
                            "update_time",
                            datetime(1970, 1, 1, second=1, tzinfo=timezone.utc),
                        )

                        self._runtime_models_info = self._merge_models(
                            self._runtime_models_info, value.get("models", {})
                        )
                    except TypeError:
                        # 防止value格式不对齐可能产生的问题
                        # global_disk_cache.delete(Consts.QianfanLLMModelsListCacheKey)
                        ...
                else:
                    self._last_update_time = datetime(
                        1970, 1, 1, second=1, tzinfo=timezone.utc
                    )
        return self._runtime_models_info

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
        if kwargs.get("_no_extra_parameters", False):
            if "extra_parameters" in kwargs:
                del kwargs["extra_parameters"]
            del kwargs["_no_extra_parameters"]
        else:
            if "extra_parameters" not in kwargs:
                kwargs["extra_parameters"] = {}
            if kwargs["extra_parameters"].get("request_source") is None:
                kwargs["extra_parameters"][
                    "request_source"
                ] = f"qianfan_py_sdk_v{VERSION}"
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
        config = self.config
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
        use_custom_endpoint: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        init resource
        """
        super().__init__(**kwargs)
        self._model = model
        self._endpoint = endpoint
        self._client = create_api_requestor(**kwargs)
        self.use_custom_endpoint = use_custom_endpoint

    def _update_model_and_endpoint(
        self, model: Optional[str], endpoint: Optional[str]
    ) -> Tuple[Optional[str], str]:
        """
        update model and endpoint passed in do with
        params passed in constructor __init__
        """
        # if user do not provide new model and endpoint,
        # use the model and endpoint from constructor
        if model is None and endpoint is None:
            model = self._model
            endpoint = self._endpoint
        if endpoint is None:
            # 获取本地模型列表
            final_model = self._default_model() if model is None else model
            model_info_list = {k.lower(): v for k, v in self._local_models().items()}
            model_info = model_info_list.get(final_model.lower())
            if model_info is None:
                # 动态获取
                model_info = self.get_model_info(final_model)
                if model_info is None:
                    raise errors.InvalidArgumentError(
                        f"The provided model `{model}` is not in the list of supported"
                        " models. If this is a recently added model, try using the"
                        " `endpoint` arguments and create an issue to tell us."
                        f" Supported models: {self.models()}"
                    )
            endpoint = model_info.endpoint
        else:
            # 适配非公有云等不需要添加chat/等前缀的endpoint
            if self.use_custom_endpoint or self.config.USE_CUSTOM_ENDPOINT:
                return model, endpoint
            endpoint = self._convert_endpoint(model, endpoint)
        return model, endpoint

    def _request(
        self,
        model: Optional[str],
        stream: bool,
        retry_config: RetryConfig,
        show_total_latency: bool = False,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        qianfan resource basic do

        Args:
            **kwargs (dict): kv dict data。

        """
        endpoint = self._extract_endpoint(**kwargs)

        # 通过model，endpoint以及模型列表获取实际的model和endpoint
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
                    show_total_latency=show_total_latency,
                )
            except errors.APIError as e:
                if (
                    e.error_code == APIErrorCode.UnsupportedMethod
                    and not refreshed_model_list
                ):
                    list = self.get_latest_api_type_models(True)
                    endpoint = list.get(model)
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
        show_total_latency: bool = False,
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
                    show_total_latency=show_total_latency,
                )
            except errors.APIError as e:
                if (
                    e.error_code == APIErrorCode.UnsupportedMethod
                    and not refreshed_model_list
                ):
                    list = self.get_latest_api_type_models(True)
                    endpoint = list.get(model)
                    refreshed_model_list = True
                    continue
                else:
                    raise e
            break
        return resp

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
        """
        models provide for resources

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        return cls()._self_supported_models()

    def _self_supported_models(self) -> Dict[str, QfLLMInfo]:
        """
        preset model services list of current config

        Args:
            None

        Returns:
            Dict[str, QfLLMInfo]: _description_
        """
        info_list = self._local_models()
        # 获取最新的模型列表
        info_list = self._merge_local_models_with_latest(info_list)
        return info_list

    def _merge_local_models_with_latest(
        self, info_list: Dict[str, QfLLMInfo]
    ) -> Dict[str, QfLLMInfo]:
        # 获取最新的模型列表
        latest_models_list = self.get_latest_api_type_models()
        for m in latest_models_list:
            if m not in info_list:
                info_list[m] = latest_models_list[m]
            else:
                # 更新endpoint
                info_list[m].endpoint = latest_models_list[m].endpoint

        return info_list

    def get_latest_api_type_models(
        self, refresh_force: bool = False
    ) -> Dict[str, QfLLMInfo]:
        return self._get_latest_supported_models(refresh_force=refresh_force).get(
            self.api_type(), {}
        )

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
            model_info = self._self_supported_models()[UNSPECIFIED_MODEL]
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

    @utils.class_or_instancemethod  # type: ignore
    def models(
        self_or_cls,
    ) -> Set[str]:
        if isinstance(self_or_cls, type):
            cls = self_or_cls
            models = set(cls._supported_models().keys())
        else:
            self = self_or_cls
            models = set(self._self_supported_models().keys())
        if UNSPECIFIED_MODEL in models:
            models.remove(UNSPECIFIED_MODEL)
        return models

    def _local_models(self) -> Dict[str, QfLLMInfo]:
        return {}

    def get_model_info(self, model: str) -> QfLLMInfo:
        """
        Get the model info of `model`

        Args:
            model (str): the name of the model,

        Return:
            Information of the model
        """
        models_info = self._self_supported_models()
        # get the supported_models list
        model_info_list = {k.lower(): v for k, v in models_info.items()}
        model_info = model_info_list.get(model.lower())
        if model_info is None:
            use_iam_aksk_msg = ""
            if self.config.ACCESS_KEY is None or self.config.SECRET_KEY is None:
                use_iam_aksk_msg = (
                    "might use `QIANFAN_ACCESS_KEY` and `QIANFAN_SECRET_KEY` instead to"
                    " get complete features supported."
                )
            raise errors.InvalidArgumentError(
                f"The provided model `{model}` is not in the list of supported models."
                " If this is a recently added model, try using the `endpoint`"
                " arguments and create an issue to tell us. Supported models:"
                f" {models_info.keys()} {use_iam_aksk_msg}"
            )
        return model_info

    def _get_latest_supported_models(
        self,
        refresh_force: bool = False,
        update_interval: Optional[float] = None,
    ) -> Dict[str, Dict[str, QfLLMInfo]]:
        """
        fetch supported models from server if `_last_update_time` is expired
        and update the `_runtime_models_info`
        """
        if self.config.ACCESS_KEY is None or self.config.SECRET_KEY is None:
            return {}

        if self.config.ENABLE_PRIVATE:
            # 私有化直接跳过
            return {}
        # try recover from cache
        self._init_model_info_with_cache()
        with self._model_infos_access_lock:
            if update_interval is None:
                update_interval = self.config.ACCESS_TOKEN_REFRESH_MIN_INTERVAL

            if (
                datetime.now(timezone.utc) - self._last_update_time
            ).total_seconds() >= update_interval or refresh_force:
                if (
                    datetime.now(timezone.utc) - self._last_update_time
                ).total_seconds() < update_interval and not refresh_force:
                    return self._runtime_models_info
                try:
                    svc_list = Service.list()["result"]["common"]
                except Exception as e:
                    log_warn(f"fetch_supported_models failed: {e}")
                    self._last_update_time = datetime.now(timezone.utc)
                    return self._runtime_models_info

                # get preset services:
                for s in svc_list:
                    try:
                        splits = s["url"].split("/")
                        api_type, model_endpoint = splits[-2], splits[-1]
                        model_info = self._runtime_models_info.get(api_type)
                        if model_info is None:
                            model_info = {}
                        model_info[s["name"]] = QfLLMInfo(
                            endpoint="/{}/{}".format(api_type, model_endpoint),
                            api_type=api_type,
                        )
                        self._runtime_models_info[api_type] = model_info
                        self._last_update_time = datetime.now(timezone.utc)
                    except Exception:
                        continue
                cache = KvCache()
                cache.set(
                    key=Consts.QianfanLLMModelsListCacheKey,
                    value=BaseResource.format_model_infos_cache(
                        self._runtime_models_info, self._last_update_time
                    ),
                )
            return self._runtime_models_info


class BaseResourceV2(BaseResource):
    def __init__(
        self,
        model: Optional[str] = None,
        app_id: Optional[str] = None,
        bearer_token: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._model = model
        self._app_id = app_id or self.config.APP_ID
        self._bearer_token = bearer_token
        self._client = QfAPIV2Requestor(**kwargs)

    def _request(
        self,
        model: Optional[str],
        stream: bool,
        retry_config: RetryConfig,
        show_total_latency: bool = False,
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
            show_total_latency=show_total_latency,
        )

        return resp

    def _generate_header(
        self, model: Optional[str], stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate header
        """

        base_headers = super()._generate_header(model, stream, **kwargs)
        if self._app_id and "app_id" not in base_headers:
            base_headers["appid"] = self._app_id
        return base_headers

    async def _arequest(
        self,
        model: Optional[str],
        stream: bool,
        retry_config: RetryConfig,
        show_total_latency: bool = False,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        resp = await self._client.async_llm(
            endpoint=self._api_path(),
            header=self._generate_header(model, stream, **kwargs),
            query=self._generate_query(model, stream, **kwargs),
            body=self._generate_body(model, stream, **kwargs),
            stream=stream,
            retry_config=retry_config,
            show_total_latency=show_total_latency,
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
        body["model"] = body["model"].lower()
        return body

    @classmethod
    def _default_model(cls) -> str:
        raise NotImplementedError

    def _api_path(self) -> str:
        raise NotImplementedError
