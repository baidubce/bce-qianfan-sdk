#!/usr/bin/env python3
"""
流式请求 统计首token延迟时间（TTFT: time to first token）
"""
import json
import os
import time
from typing import Optional

import requests
from locust import constant, events, task
from locust.clients import ResponseContextManager
from locust.env import Environment
from locust.exception import LocustError
from locust.stats import RequestStats
from urllib3 import PoolManager

import qianfan
from qianfan.dataset import Dataset
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
    request_type,
    name,
    response_time,
    response_length,
    exception=None,
    **kwargs
):
    """
    每个请求均会调用，用于向统计表注册数据
    (1) 注册1个记录：stats.log_request(request_type, name, time, length)
    (2) 标记为失败或某种分类：stats.log_error(request_type, name, exc)  其中exc为错误或分类message，最终会按type+name+exc分类统计
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
    request_type,
    name,
    response_time,
    response_length,
    exception=None,
    **kwargs
):
    if "input_tokens" in kwargs:
        stats.log_request(request_type, name, kwargs["input_tokens"], response_length)
    else:
        stats.log_request(request_type, name, 0, response_length)
        stats.log_error(request_type, name, "未找到输入token数")


def output_tokens_request_handler(
    stats: RequestStats,
    request_type,
    name,
    response_time,
    response_length,
    exception=None,
    **kwargs
):
    if "output_tokens" in kwargs:
        stats.log_request(request_type, name, kwargs["output_tokens"], response_length)
    else:
        stats.log_request(request_type, name, 0, response_length)
        stats.log_error(request_type, name, "未找到输出token数")


# (1) 上文统计ttft的方法request_handler 是CustomHandler的默认行为；
#     如需此场景 可无需传入request_handler参数，即：CustomHandler()
# (2) 上文平均时间的阈值判断方法condition_handler 是CustomHandler.add_listener的默认行为；
#     如需此场景 可无需传入condition_handler参数，即：CustomHandler(xxx).add_listener(thresholds=xxx)
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

    exc = None

    def __init__(
        self,
        model,
        request_event,
        user,
        *args,
        pool_manager: Optional[PoolManager] = None,
        **kwargs
    ):
        """
        init
        """
        super().__init__(
            model, request_event, user, *args, pool_manager=pool_manager, **kwargs
        )
        self.model = model
        self.chat_comp = qianfan.ChatCompletion(model=model)

    def _request_internal(self, context=None, messages=None, **kwargs):
        context = context or {}
        messages = messages or []
        first_flag = True
        request_meta = {
            "input_tokens": 0,
            "output_tokens": 0,
            "response_length": 0,
            "request_length": sum([len(msg) for msg in messages]),
        }
        last_resp = None
        all_empty = True

        start_time = time.time()
        start_perf_counter = time.perf_counter()
        responses = self.chat_comp.do(messages=messages, **kwargs)
        for resp in responses:
            resp.url = self.model
            resp.reason = None
            resp.status_code = resp["code"]

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

    def request(self, messages=None, context=None, **kwargs):
        """
        Constructs and sends a :py:class:`requests.Request`.
        Returns :py:class:`requests.Response` object.
        """
        context = context or {}
        self.exc = None

        request_meta = self._request_internal(
            context=context, messages=messages, **kwargs
        )

        with ResponseContextManager(
            request_meta["response"],
            request_event=self.request_event,
            request_meta=request_meta,
        ) as rcm:
            pass


@events.test_start.add_listener
def test_start(environment: Environment, **kwargs):
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

    # ds = Dataset.load(data_file="./lxtest.jsonl")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.host is None:
            raise LocustError(
                "You must specify the base host. Either in the host attribute in the"
                " User class, "
                + "or on the command line using the --host option."
            )

        self.client = QianfanCustomHttpSession(
            model=self.host,
            request_event=self.environment.events.request,
            user=self,
            pool_manager=self.pool_manager,
        )
        """
        Instance of HttpSession that is created upon instantiation of Locust.
        The client supports cookies, and therefore keeps the session between HTTP requests.
        """
        self.client.trust_env = False
        self.query_idx = 0

    @task
    def mytask(self):
        hyperparameters = GlobalData.data["hyperparameters"]
        data = next(distributor)
        if isinstance(data, list):
            messages = self._load_jsonl(data)
        elif isinstance(data, dict):
            messages = self._load_json(data)
        elif isinstance(data, str):
            messages = self._load_txt(data)
        else:
            raise Exception("Data format unsupported.")
        if hyperparameters is None:
            hyperparameters = {}
        self.client.request(messages=messages, stream=True, **hyperparameters)

    def _load_jsonl(self, data):
        messages = [] 
        for d in data:
           msg = {
               "role": "user",
               "content": d["prompt"]
           }
           messages.append(msg)
           if "response" in d:
               msg = {
                   "role": "assistant",
                   "content": d["response"]
               }
               messages.append(msg)
        if messages[-1]["role"] == "assistant":
            messages.pop(-1)
        return messages

    def _load_json(self, data):
        messages = []
        msg = {
            "role": "user",
            "content": data["prompt"]
        }
        messages.append(msg)
        return messages

    def _load_txt(self, data):
        messages = []
        msg = {
            "role": "user",
            "content": data
        }
        messages.append(msg)
        return messages
