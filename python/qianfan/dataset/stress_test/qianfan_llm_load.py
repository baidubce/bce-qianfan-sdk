#!/usr/bin/env python3
"""
流式请求 统计首token延迟时间（TTFT: time to first token）
"""
import abc
import json
import re
import time
from typing import Any, Dict, Iterator, Literal, Optional

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
    **kwargs: Any,
) -> None:
    """
    每个请求均会调用，用于向统计表注册数据
    (1) 注册1个记录：stats.log_request(request_type, name, time, length)
    (2) 标记为失败或某种分类：stats.log_error(request_type, name, exc)
        其中exc为错误或分类message，最终会按type+name+exc分类统计
    """
    if "first_token_latency" in kwargs:
        stats.log_request(
            request_type, name, kwargs["first_token_latency"] * 1000, response_length
        )
    else:
        stats.log_error(request_type, name, "未找到首token延迟指标")


def input_tokens_request_handler(
    stats: RequestStats,
    request_type: str,
    name: str,
    response_time: int,
    response_length: int,
    exception: Optional[Exception] = None,
    **kwargs: Any,
) -> None:
    if "input_tokens" in kwargs:
        stats.log_request(request_type, name, kwargs["input_tokens"], response_length)
    else:
        stats.log_error(request_type, name, "未找到输入token数")


def output_tokens_request_handler(
    stats: RequestStats,
    request_type: str,
    name: str,
    response_time: int,
    response_length: int,
    exception: Optional[Exception] = None,
    **kwargs: Any,
) -> None:
    if "output_tokens" in kwargs:
        stats.log_request(request_type, name, kwargs["output_tokens"], response_length)
    else:
        stats.log_error(request_type, name, "未找到输出token数")


def interval_latency_handler(
    stats: RequestStats,
    request_type: str,
    name: str,
    response_time: int,
    response_length: int,
    exception: Optional[Exception] = None,
    **kwargs: Any,
) -> None:
    if "request_latency" in kwargs:
        for latency in kwargs["request_latency"]:
            stats.log_request(request_type, name, latency * 1000, response_length)
    else:
        stats.log_error(request_type, name, "未找到包间延迟")


def input_str_length_handler(
    stats: RequestStats,
    request_type: str,
    name: str,
    response_time: int,
    response_length: int,
    exception: Optional[Exception] = None,
    **kwargs: Any,
) -> None:
    if "request_length" in kwargs:
        stats.log_request(request_type, name, kwargs["request_length"], response_length)
    else:
        stats.log_error(request_type, name, "未找到请求长度")


def output_str_length_handler(
    stats: RequestStats,
    request_type: str,
    name: str,
    response_time: int,
    response_length: int,
    exception: Optional[Exception] = None,
    **kwargs: Any,
) -> None:
    if "output_response_length" in kwargs:
        stats.log_request(
            request_type, name, kwargs["output_response_length"], response_length
        )
    else:
        stats.log_error(request_type, name, "未找到输出长度")


def total_latency_handler(
    stats: RequestStats,
    request_type: str,
    name: str,
    response_time: int,
    response_length: int,
    exception: Optional[Exception] = None,
    **kwargs: Any,
) -> None:
    if "total_latency" in kwargs:
        stats.log_request(request_type, name, kwargs["total_latency"], response_length)
    else:
        stats.log_error(request_type, name, "未找到请求耗时")


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

CustomHandler(
    name="包间延迟统计",
    request_handler=interval_latency_handler,
    csv_suffix="interval_latency",
)

CustomHandler(
    name="输入长度延迟统计",
    request_handler=input_str_length_handler,
    csv_suffix="input_str_length",
)

CustomHandler(
    name="输出长度延迟统计",
    request_handler=output_str_length_handler,
    csv_suffix="output_str_length",
)

CustomHandler(
    name="请求耗时统计",
    request_handler=total_latency_handler,
    csv_suffix="total_latency",
)

_remove_access_token_pattern = re.compile(r"([&?])access_token=[^&]*(&)?")


def _remove_access_token_url_parameter(url: str) -> str:
    # 使用正则表达式替换参数，注意分组用于保留正确连接符号
    new_url = _remove_access_token_pattern.sub(
        lambda m: m.group(1) if m.group(2) else "", url
    )

    # 移除可能遗留在结尾的 '&' 或 '?'
    if new_url.endswith("?") or new_url.endswith("&"):
        new_url = new_url[:-1]

    return new_url


class _InnerResponseProcessRet:
    def __init__(
        self, request_meta: Dict, last_resp: Optional[QfResponse], merged_result: str
    ):
        self.request_meta = request_meta
        self.last_resp = last_resp
        self.merged_result = merged_result


class QianfanCustomHttpSession(CustomHttpSession):
    """
    custom http session class
    """

    exc: Optional[Exception] = None
    model: str = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._file_lock: Any = GlobalData.data["file_lock"]
        super().__init__(*args, **kwargs)

    def _request_internal(
        self, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        context = context or {}
        start_time = time.time()
        res: Dict = {}
        request_meta = self._prepare_request_meta(context, **kwargs)

        try:
            kwargs["retry_count"] = 0
            responses = self._get_request(context, **kwargs)
            processed_resp = self._process_responses(responses, request_meta)

            last_resp = processed_resp.last_resp
            request_meta = processed_resp.request_meta

            assert last_resp is not None
            res = {
                "headers": last_resp.headers,
                "stat": last_resp.statistic,
                "body": last_resp.body,
            }
            res["body"]["result"] = processed_resp.merged_result
            request_meta["output_response_length"] = len(processed_resp.merged_result)
            request_meta["total_latency"] = last_resp.statistic["total_latency"] * 1000
        except Exception as e:
            self.exc = e
            resp = QfResponse(-1)
            last_resp = resp
            setattr(resp, "url", self.model)
            setattr(resp, "reason", str(e))
            setattr(resp, "status_code", 500)

        if self.exc is None and last_resp is not None and last_resp.request is not None:
            res["request"] = last_resp.request.requests_args()

        if GlobalData.data["log"] == 1:
            if self.exc:
                self._write_result({"error": str(self.exc)})
            else:
                if (
                    res.get("request", {}).get("headers", {}).get("Authorization", None)
                    is not None
                ):
                    del res["request"]["headers"]["Authorization"]

                if len(res.get("request", {}).get("url", "")) != 0:
                    res["request"]["url"] = _remove_access_token_url_parameter(
                        res["request"]["url"]
                    )

                self._write_result(res)

        if self.user:
            context = {**self.user.context(), **context}
        if self.exc is None:
            # report succeed to locust's statistics
            assert last_resp is not None
            request_meta["request_type"] = "POST"
            request_meta["response_time"] = (
                last_resp.statistic.get("total_latency", 0) * 1000
            )
            request_meta["name"] = self.model
            request_meta["context"] = context
            request_meta["exception"] = self.exc
            request_meta["start_time"] = start_time
            request_meta["url"] = self.model
            request_meta["response"] = last_resp
        else:
            # setting response_time to None when the request is failed
            request_meta["response_time"] = None
            request_meta["request_type"] = "POST"
            request_meta["name"] = self.model
            request_meta["context"] = context
            request_meta["exception"] = self.exc
            request_meta["start_time"] = start_time
            request_meta["url"] = self.model
            request_meta["response"] = last_resp
        return request_meta

    @abc.abstractmethod
    def _process_responses(
        self, responses: Iterator[QfResponse], request_meta: Dict
    ) -> _InnerResponseProcessRet:
        ...

    @abc.abstractmethod
    def _prepare_request_meta(self, context: Dict, **kwargs: Any) -> Dict:
        ...

    @abc.abstractmethod
    def _get_request(self, context: Dict, **kwargs: Any) -> Iterator[QfResponse]:
        ...

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
            if input_column not in data and output_column not in data:
                ret = self._transfer_body(data)
            else:
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

    def _transfer_body(self, data: Any) -> Any:
        ...

    def _write_result(self, res: Dict) -> None:
        res_json = json.dumps(res, ensure_ascii=False)
        folder = GlobalData.data["record_dir"]
        file_path = folder + "/" + "query_result.jsonl"
        with self._file_lock:
            with open(file_path, "a") as f:
                f.write(res_json + "\n")


class ChatCompletionClient(QianfanCustomHttpSession):
    def __init__(
        self,
        model: str,
        is_endpoint: bool,
        request_event: Any,
        user: Any,
        *args: Any,
        pool_manager: Optional[PoolManager] = None,
        version: Literal["1", "2", 1, 2] = "1",
        app_id: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        init
        """
        super().__init__(
            model, request_event, user, *args, pool_manager=pool_manager, **kwargs
        )
        self.model = model
        self.is_v2 = str(version) == "2"

        if is_endpoint:
            if self.is_v2:
                raise ValueError("v2 api doesn't support endpoint")

            self.chat_comp = qianfan.ChatCompletion(
                endpoint=model,
                forcing_disable=True,
                **kwargs,
            )
        else:
            if self.is_v2:
                self.chat_comp = qianfan.ChatCompletion(
                    version="2",
                    model=model,
                    forcing_disable=True,
                    app_id=app_id,
                    **kwargs,
                )
            else:
                self.chat_comp = qianfan.ChatCompletion(
                    model=model, forcing_disable=True, **kwargs
                )

    def _process_responses(
        self, responses: Iterator[QfResponse], request_meta: Dict
    ) -> _InnerResponseProcessRet:
        last_resp: Optional[QfResponse] = None
        merged_query = ""
        first_flag, all_empty = True, True
        clear_history = False

        for resp in responses:
            last_resp = resp
            setattr(resp, "url", self.model)
            setattr(resp, "reason", None)
            setattr(resp, "status_code", resp["code"])

            # 计算token数, 有usage的累加，没有的直接计算content
            if "usage" in resp.body and resp.body["usage"] is not None:
                request_meta["input_tokens"] = int(resp.body["usage"]["prompt_tokens"])
                request_meta["output_tokens"] = int(
                    resp.body["usage"]["completion_tokens"]
                )
            else:
                request_meta["input_tokens"] = request_meta["request_length"]
                request_meta["output_tokens"] = 0

            if first_flag:
                request_meta["first_token_latency"] = resp.statistic[
                    "first_token_latency"
                ]
                if "first_latency_threshold" in GlobalData.data:
                    if (
                        request_meta["first_token_latency"]
                        > GlobalData.data["first_latency_threshold"]
                    ):
                        GlobalData.data["threshold_first"].value = 1
                first_flag = False

            interval_latencies = request_meta.get("request_latency", [])
            interval_latencies.append(resp.statistic["request_latency"])
            request_meta["request_latency"] = interval_latencies

            if not self.is_v2:
                stream_json = resp["body"]
                merged_query += stream_json.get("result", "")
                clear_history = stream_json.get("need_clear_history", False)
                if "result" in stream_json:
                    content = stream_json["result"]
                elif "error_code" in stream_json and stream_json["error_code"] > 0:
                    self.exc = Exception(
                        "ERROR CODE {}".format(str(stream_json["error_code"]))
                    )
                    break
                else:
                    self.exc = Exception("ERROR CODE 结果无法解析")
                    break
            else:
                if "error_code" in resp.body and resp.body["error_code"] > 0:
                    self.exc = Exception(
                        "ERROR CODE {}".format(str(resp.body["error_code"]))
                    )
                    break

                if len(resp.body["choices"]) == 0:
                    break

                stream_json = resp.body["choices"][0]
                clear_history = stream_json.get("need_clear_history", False)
                if "delta" in stream_json:
                    content = stream_json["delta"].get("content", "")
                    merged_query += content
                else:
                    self.exc = Exception("ERROR CODE 结果无法解析")
                    break

            if len(content) != 0:
                all_empty = False

        assert last_resp is not None
        if all_empty and not clear_history:
            self.exc = Exception("Response is empty")
        elif last_resp is None and self.exc is None:
            self.exc = Exception("Response is null")
        elif not self.is_v2 and "is_end" not in last_resp["body"]:
            self.exc = Exception("Response not finished")
        elif last_resp["code"] != 200 or (
            not self.is_v2 and not last_resp["body"]["is_end"]
        ):
            self.exc = Exception("NOT 200 OR is_end is False")

        return _InnerResponseProcessRet(request_meta, last_resp, merged_query)

    def _get_request(self, context: Dict, **kwargs: Any) -> Iterator[QfResponse]:
        if "messages" in kwargs:
            messages = kwargs.pop("messages")
        else:
            messages = []

        responses = self.chat_comp.do(messages=messages, **kwargs)
        assert isinstance(responses, Iterator)
        return responses

    def _prepare_request_meta(self, context: Dict, **kwargs: Any) -> Dict:
        if "messages" in kwargs:
            messages = kwargs.pop("messages")
        else:
            messages = []

        request_meta: Dict[str, Any] = {
            "response_length": 0,
            "request_length": sum([len(msg) for msg in messages]),
        }

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

    def _transfer_body(self, data: Any) -> Any:
        ret = data
        if "stream" in ret:
            del ret["stream"]
        if "safety_level" in ret and ret["safety_level"] == "none":
            del ret["safety_level"]
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
        version: Literal["1", "2", 1, 2] = "1",
        app_id: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        init
        """
        super().__init__(
            model, request_event, user, *args, pool_manager=pool_manager, **kwargs
        )
        self.model = model
        self.is_v2 = str(version) == "2"

        if is_endpoint:
            if self.is_v2:
                raise ValueError("v2 api doesn't support endpoint")
            else:
                self.comp = qianfan.Completion(endpoint=model, **kwargs)
        else:
            if self.is_v2:
                self.comp = qianfan.Completion(
                    version="2",
                    model=model,
                    app_id=app_id,
                    forcing_disable=True,
                    **kwargs,
                )
            else:
                self.comp = qianfan.Completion(
                    model=model, forcing_disable=True, **kwargs
                )

    def _process_responses(
        self, responses: Iterator[QfResponse], request_meta: Dict
    ) -> _InnerResponseProcessRet:
        last_resp: Optional[QfResponse] = None
        merged_query = ""
        first_flag = True

        for resp in responses:
            last_resp = resp
            setattr(resp, "url", self.model)
            setattr(resp, "reason", None)
            setattr(resp, "status_code", resp["code"])

            # 计算token数, 有usage的累加，没有的直接计算content
            if "usage" in resp.body and resp.body["usage"] is not None:
                request_meta["input_tokens"] = int(resp.body["usage"]["prompt_tokens"])
                request_meta["output_tokens"] = int(
                    resp.body["usage"]["completion_tokens"]
                )
            else:
                request_meta["input_tokens"] = request_meta["request_length"]
                request_meta["output_tokens"] = 0

            stream_json = resp["body"]
            merged_query += stream_json["result"]
            if first_flag:
                request_meta["first_token_latency"] = resp.statistic[
                    "first_token_latency"
                ]
                if (
                    request_meta["first_token_latency"]
                    > GlobalData.data["first_latency_threshold"]
                ):
                    GlobalData.data["threshold_first"].value = 1
                first_flag = False

            interval_latencies = request_meta.get("request_latency", [])
            interval_latencies.append(resp.statistic["request_latency"])
            request_meta["request_latency"] = interval_latencies

            if "result" not in stream_json:
                self.exc = Exception("ERROR CODE 结果无法解析")
                break
            if "error_code" in stream_json and stream_json["error_code"] > 0:
                self.exc = Exception(
                    "ERROR CODE {}".format(str(stream_json["error_code"]))
                )
                break

        return _InnerResponseProcessRet(request_meta, last_resp, merged_query)

    def _get_request(self, context: Dict, **kwargs: Any) -> Iterator[QfResponse]:
        if "prompt" in kwargs:
            prompt = kwargs.pop("prompt")
        else:
            prompt = ""

        responses = self.comp.do(prompt=prompt, **kwargs)
        assert isinstance(responses, Iterator)
        return responses

    def _prepare_request_meta(self, context: Dict, **kwargs: Any) -> Dict:
        if "prompt" in kwargs:
            prompt = kwargs.pop("prompt")
        else:
            prompt = ""

        request_meta: Dict[str, Any] = {
            "response_length": 0,
            "request_length": len(prompt),
        }

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

    def _transfer_body(self, data: Any) -> Any:
        p = data["messages"][0]["content"]
        return dict(prompt=p)


@events.test_start.add_listener
def test_start(environment: Environment, **kwargs: Any) -> None:
    """
    注册分布式数据集
    """
    global distributor
    dataset = GlobalData.data["dataset"]
    dataset = dataset.list()
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

        app_id = GlobalData.data.get("app_id", None)
        version = GlobalData.data.get("version", "1")

        self.client: QianfanCustomHttpSession
        if model_type == "ChatCompletion":
            self.client = ChatCompletionClient(
                model=self.host,
                is_endpoint=is_endpoint,
                request_event=self.environment.events.request,
                user=self,
                pool_manager=self.pool_manager,
                version=version,
                app_id=app_id,
                **kwargs,
            )
        elif model_type == "Completion":
            self.client = CompletionClient(  # noqa
                model=self.host,
                is_endpoint=is_endpoint,
                request_event=self.environment.events.request,
                user=self,
                pool_manager=self.pool_manager,
                version=version,
                app_id=app_id,
                **kwargs,
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
        self.query_idx += 1
        body = self.client.transfer_data(data, self.input_column, self.output_column)
        if hyperparameters is None:
            hyperparameters = {}
        # 参数去重
        keys_to_delete = [key for key in hyperparameters.keys() if key in body]
        for key in keys_to_delete:
            del hyperparameters[key]
        self.client.qianfan_request(
            show_total_latency=True, stream=True, **body, **hyperparameters
        )
