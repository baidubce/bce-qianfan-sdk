#!/usr/bin/env python3
"""
流式请求 统计首token延迟时间（TTFT: time to first token）
"""
import time
from typing import Any, Dict, Optional

from locust import constant, events, task
from locust.clients import ResponseContextManager
from locust.env import Environment
from locust.exception import LocustError
from locust.stats import RequestStats
from urllib3 import PoolManager

import qianfan
from qianfan import QfResponse
from qianfan.dataset.stress_test.yame import GlobalData
from qianfan.dataset.stress_test.yame.distributor import Distributor
from qianfan.dataset.stress_test.yame.listeners import CustomHandler
from qianfan.dataset.stress_test.yame.users.custom_user import (
    CustomHttpSession,
    CustomUser,
)
from qianfan.utils import disable_log

disable_log()


distributor = None


def first_token_latency_request_handler(
    stats: RequestStats,
    request_type: str,
    name: str,
    response_time: int,
    response_length: int,
    exception: Optional[Exception] = None,
    **kwargs: Any
) -> None:
    """
    每个请求均会调用，用于向统计表注册数据
    (1) 注册1个记录：stats.log_request(request_type, name, time, length)
    (2) 标记为失败或某种分类：stats.log_error(request_type, name, exc)
        其中exc为错误或分类message，最终会按type+name+exc分类统计
    """
    if "first_token_latency" in kwargs:
        stats.log_request(
            request_type, name, kwargs["first_token_latency"], response_length
        )
    else:
        stats.log_request(request_type, name, 0, response_length)
        stats.log_error(request_type, name, "未找到首token延迟指标")


def input_tokens_request_handler(
    stats: RequestStats,
    request_type: str,
    name: str,
    response_time: int,
    response_length: int,
    exception: Optional[Exception] = None,
    **kwargs: Any
) -> None:
    if "input_tokens" in kwargs:
        stats.log_request(request_type, name, kwargs["input_tokens"], response_length)
    else:
        stats.log_request(request_type, name, 0, response_length)
        stats.log_error(request_type, name, "未找到输入token数")


def output_tokens_request_handler(
    stats: RequestStats,
    request_type: str,
    name: str,
    response_time: int,
    response_length: int,
    exception: Optional[Exception] = None,
    **kwargs: Any
) -> None:
    if "output_tokens" in kwargs:
        stats.log_request(request_type, name, kwargs["output_tokens"], response_length)
    else:
        stats.log_request(request_type, name, 0, response_length)
        stats.log_error(request_type, name, "未找到输出token数")


# (1) 上文统计ttft的方法request_handler 是CustomHandler的默认行为；
#     如需此场景 可无需传入request_handler参数，即：CustomHandler()
# (2) 上文平均时间的阈值判断方法condition_handler
#     是CustomHandler.add_listener的默认行为；
#     如需此场景 可无需传入condition_handler参数，
#     即：CustomHandler(xxx).add_listener(thresholds=xxx)
CustomHandler(
    name="首token延迟时间统计",
    request_handler=first_token_latency_request_handler,
    csv_suffix="first_token_latency",
)
CustomHandler(
    name="输入token数统计",
    request_handler=input_tokens_request_handler,
    csv_suffix="input_tokens",
)
CustomHandler(
    name="输出token数统计",
    request_handler=output_tokens_request_handler,
    csv_suffix="output_tokens",
)


class QianfanCustomHttpSession(CustomHttpSession):
    """
    custom http session class
    """

    exc: Optional[Exception] = None

    def _request_internal(
        self, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        return {}

    def qianfan_request(
        self, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        """
        Constructs and sends a :py:class:`requests.Request`.
        Returns :py:class:`requests.Response` object.
        """
        context = context or {}
        self.exc = None

        request_meta = self._request_internal(context=context, **kwargs)

        with ResponseContextManager(
            request_meta["response"],
            request_event=self.request_event,
            request_meta=request_meta,
        ):
            pass

    def transfer_data(self, data: Any, input_column: str, output_column: str) -> Any:
        if isinstance(data, list):
            ret = self._transfer_jsonl(
                data, input_column=input_column, output_column=output_column
            )
        elif isinstance(data, dict):
            ret = self._transfer_json(
                data, input_column=input_column, output_column=output_column
            )
        elif isinstance(data, str):
            ret = self._transfer_txt(
                data, input_column=input_column, output_column=output_column
            )
        else:
            raise Exception("Data format unsupported.")
        return ret

    def _transfer_jsonl(
        self, data: Any, input_column: str, output_column: str, **kwargs: Any
    ) -> Any:
        ...

    def _transfer_json(
        self, data: Any, input_column: str, output_column: str, **kwargs: Any
    ) -> Any:
        ...

    def _transfer_txt(
        self, data: Any, input_column: str, output_column: str, **kwargs: Any
    ) -> Any:
        ...


class ChatCompletionClient(QianfanCustomHttpSession):
    def __init__(
        self,
        model: str,
        is_endpoint: bool,
        request_event: Any,
        user: Any,
        *args: Any,
        pool_manager: Optional[PoolManager] = None,
        **kwargs: Any
    ):
        """
        init
        """
        super().__init__(
            model, request_event, user, *args, pool_manager=pool_manager, **kwargs
        )
        self.model = model
        if is_endpoint:
            self.chat_comp = qianfan.ChatCompletion(endpoint=model)
        else:
            self.chat_comp = qianfan.ChatCompletion(model=model)

    def _request_internal(
        self, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        context = context or {}
        if "messages" in kwargs:
            messages = kwargs.pop("messages")
        else:
            messages = []
        first_flag = True
        request_meta: Dict[str, Any] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "response_length": 0,
            "request_length": sum([len(msg) for msg in messages]),
        }
        last_resp = None
        all_empty = True

        start_time = time.time()
        start_perf_counter = time.perf_counter()
        try:
            kwargs["retry_count"] = 0
            responses = self.chat_comp.do(messages=messages, **kwargs)
        except Exception as e:
            self.exc = e
            resp = QfResponse(-1)
            last_resp = resp
            setattr(resp, "url", self.model)
            setattr(resp, "reason", str(e))
            setattr(resp, "status_code", 500)

        if self.exc is None:
            for resp in responses:
                setattr(resp, "url", self.model)
                setattr(resp, "reason", None)
                setattr(resp, "status_code", resp["code"])

                stream_json = resp["body"]
                clear_history = stream_json.get("need_clear_history", False)
                if first_flag:
                    request_meta["first_token_latency"] = (
                        time.perf_counter() - start_perf_counter
                    ) * 1000  # 首Token延迟
                    first_flag = False
                content = ""
                if "result" in stream_json:
                    content = stream_json["result"]
                else:
                    self.exc = Exception("ERROR CODE 结果无法解析")
                    break
                if "error_code" in stream_json and stream_json["error_code"] > 0:
                    self.exc = Exception(
                        "ERROR CODE {}".format(str(stream_json["error_code"]))
                    )
                    break
                if len(content) != 0:
                    all_empty = False
                # 计算token数, 有usage的累加，没有的直接计算content
                if "usage" in stream_json:
                    request_meta["input_tokens"] = int(
                        stream_json["usage"]["prompt_tokens"]
                    )
                    request_meta["output_tokens"] = int(
                        stream_json["usage"]["completion_tokens"]
                    )
                else:
                    request_meta["input_tokens"] = request_meta["request_length"]
                    request_meta["output_tokens"] = request_meta["response_length"]
                last_resp = resp

            assert last_resp is not None
            if all_empty and not clear_history:
                self.exc = Exception("Response is empty")
            elif last_resp is None and self.exc is None:
                self.exc = Exception("Response is null")
            elif "is_end" not in last_resp["body"]:
                self.exc = Exception("Response not finished")
            elif last_resp["code"] != 200 or not last_resp["body"]["is_end"]:
                self.exc = Exception("NOT 200 OR is_end is False")

        response_time = (time.perf_counter() - start_perf_counter) * 1000
        if self.user:
            context = {**self.user.context(), **context}

        # store meta data that is used when reporting the request to locust's statistics
        request_meta["request_type"] = "POST"
        request_meta["response_time"] = response_time
        request_meta["name"] = self.model
        request_meta["context"] = context
        request_meta["exception"] = self.exc
        request_meta["start_time"] = start_time
        request_meta["url"] = self.model
        request_meta["response"] = last_resp
        return request_meta

    def _transfer_jsonl(
        self, data: Any, input_column: str, output_column: str, **kwargs: Any
    ) -> Any:
        ret: Dict[str, Any] = {"messages": []}
        for d in data:
            msg = {"role": "user", "content": d[input_column]}
            ret["messages"].append(msg)
            if output_column in d:
                msg = {"role": "assistant", "content": d[output_column]}
                ret["messages"].append(msg)
        if ret["messages"][-1]["role"] == "assistant":
            ret["messages"].pop(-1)
        return ret

    def _transfer_json(
        self, data: Any, input_column: str, output_column: str, **kwargs: Any
    ) -> Any:
        ret: Dict[str, Any] = {"messages": []}
        msg = {"role": "user", "content": data[input_column]}
        ret["messages"].append(msg)
        return ret

    def _transfer_txt(
        self, data: Any, input_column: str, output_column: str, **kwargs: Any
    ) -> Any:
        ret: Dict[str, Any] = {"messages": []}
        msg = {"role": "user", "content": data}
        ret["messages"].append(msg)
        return ret


class CompletionClient(QianfanCustomHttpSession):
    def __init__(
        self,
        model: str,
        is_endpoint: bool,
        request_event: Any,
        user: Any,
        *args: Any,
        pool_manager: Optional[PoolManager] = None,
        **kwargs: Any
    ):
        """
        init
        """
        super().__init__(
            model, request_event, user, *args, pool_manager=pool_manager, **kwargs
        )
        self.model = model
        if is_endpoint:
            self.comp = qianfan.Completion(endpoint=model)
        else:
            self.comp = qianfan.Completion(model=model)

    def _request_internal(
        self, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        context = context or {}
        if "prompt" in kwargs:
            prompt = kwargs.pop("prompt")
        else:
            prompt = ""
        first_flag = True
        request_meta: Dict[str, Any] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "response_length": 0,
            "request_length": len(prompt),
        }
        last_resp = None
        all_empty = True

        start_time = time.time()
        start_perf_counter = time.perf_counter()
        responses = self.comp.do(prompt=prompt, **kwargs)
        for resp in responses:
            setattr(resp, "url", self.model)
            setattr(resp, "reason", None)
            setattr(resp, "status_code", resp["code"])

            stream_json = resp["body"]
            if first_flag:
                request_meta["first_token_latency"] = (
                    time.perf_counter() - start_perf_counter
                ) * 1000  # 首Token延迟
                first_flag = False
            content = ""
            if "result" in stream_json:
                content = stream_json["result"]
            else:
                self.exc = Exception("ERROR CODE 结果无法解析")
                break
            if "error_code" in stream_json and stream_json["error_code"] > 0:
                self.exc = Exception(
                    "ERROR CODE {}".format(str(stream_json["error_code"]))
                )
                break
            if len(content) != 0:
                all_empty = False
            # 计算token数, 有usage的累加，没有的直接计算content
            if "usage" in stream_json:
                request_meta["input_tokens"] = int(
                    stream_json["usage"]["prompt_tokens"]
                )
                request_meta["output_tokens"] = int(
                    stream_json["usage"]["total_tokens"]
                ) - int(stream_json["usage"]["prompt_tokens"])
            else:
                request_meta["input_tokens"] = request_meta["request_length"]
                request_meta["output_tokens"] = request_meta["response_length"]
            last_resp = resp

        assert last_resp is not None
        if all_empty:
            self.exc = Exception("Response is empty")
        elif last_resp is None and self.exc is None:
            self.exc = Exception("Response is null")
        elif "is_end" not in last_resp["body"]:
            self.exc = Exception("Response not finished")
        elif last_resp["code"] != 200 or not last_resp["body"]["is_end"]:
            self.exc = Exception("NOT 200 OR is_end is False")

        response_time = (time.perf_counter() - start_perf_counter) * 1000
        if self.user:
            context = {**self.user.context(), **context}

        # store meta data that is used when reporting the request to locust's statistics
        request_meta["request_type"] = "POST"
        request_meta["response_time"] = response_time
        request_meta["name"] = self.model
        request_meta["context"] = context
        request_meta["exception"] = self.exc
        request_meta["start_time"] = start_time
        request_meta["url"] = self.model
        request_meta["response"] = last_resp
        return request_meta

    def _transfer_jsonl(
        self, data: Any, input_column: str, output_column: str, **kwargs: Any
    ) -> Any:
        prompt = ""
        if len(data) > 0:
            prompt = data[0][input_column]
        return dict(prompt=prompt)

    def _transfer_json(
        self, data: Any, input_column: str, output_column: str, **kwargs: Any
    ) -> Any:
        return dict(prompt=data[input_column])

    def _transfer_txt(
        self, data: Any, input_column: str, output_column: str, **kwargs: Any
    ) -> Any:
        return dict(prompt=data)


@events.test_start.add_listener
def test_start(environment: Environment, **kwargs: Any) -> None:
    """
    注册分布式数据集
    """
    global distributor
    dataset = GlobalData.data["dataset"]
    distributor = Distributor(
        environment, iter(dataset)
    )  # Quite runner when iterator raises StopIteration.


class QianfanLLMLoadUser(CustomUser):
    """示例：统计ttft"""

    wait_time = constant(0)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        if self.host is None:
            raise LocustError(
                "You must specify the base host. Either in the host attribute in the"
                " User class, "
                + "or on the command line using the --host option."
            )

        model_type = GlobalData.data["model_type"]
        is_endpoint = GlobalData.data["is_endpoint"]
        self.client: QianfanCustomHttpSession
        if model_type == "ChatCompletion":
            self.client = ChatCompletionClient(
                model=self.host,
                is_endpoint=is_endpoint,
                request_event=self.environment.events.request,
                user=self,
                pool_manager=self.pool_manager,
            )
        elif model_type == "Completion":
            self.client = CompletionClient(  # noqa
                model=self.host,
                is_endpoint=is_endpoint,
                request_event=self.environment.events.request,
                user=self,
                pool_manager=self.pool_manager,
            )
        else:
            raise Exception("Unsupported model type: %s." % model_type)

        self.client.trust_env = False
        self.query_idx = 0

        ds = GlobalData.data["dataset"]
        self.input_column = ds.input_columns[0] if ds.input_columns else "prompt"
        self.output_column = ds.reference_column if ds.reference_column else "response"

    @task
    def mytask(self) -> None:
        hyperparameters = GlobalData.data["hyperparameters"]
        assert distributor is not None
        data = next(distributor)
        body = self.client.transfer_data(data, self.input_column, self.output_column)
        if hyperparameters is None:
            hyperparameters = {}
        self.client.qianfan_request(stream=True, **body, **hyperparameters)
