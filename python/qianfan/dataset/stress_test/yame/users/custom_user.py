#!/usr/bin/env python3
# coding=utf-8
"""
自定义User（重写HttpUser）
支持request_meta添加自定义指标（需要再添加自定义Handler处理统计）
"""
import time
from typing import Any, Dict, Optional

import requests
from locust import User
from locust.clients import HttpSession, ResponseContextManager
from locust.exception import LocustError
from urllib3 import PoolManager


class CustomUser(User):
    """
    custom http user class
    """

    abstract = True
    """If abstract is True, the class is meant to be subclassed, 
    and users will not choose this locust during a test"""

    pool_manager: Optional[PoolManager] = None
    """Connection pool manager to use. If not given, 
    a new manager is created per single user."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        if self.host is None:
            raise LocustError(
                "You must specify the base host. Either in the host attribute in the"
                " User class, "
                + "or on the command line using the --host option."
            )

        self.client = CustomHttpSession(
            base_url=self.host,
            request_event=self.environment.events.request,
            user=self,
            pool_manager=self.pool_manager,
        )
        """
        Instance of HttpSession that is created upon instantiation of Locust.
        The client supports cookies, 
        and therefore keeps the session between HTTP requests.
        """
        self.client.trust_env = False

    def set_result(
        self, response: requests.Response, start_time: float, **kwargs: Any
    ) -> Optional[Dict[Any, Any]]:
        """
        添加自定义指标数据
        :param response: request.Response
        :param start_time: 开始请求的时间，来自time.perf_counter()的结果
        :param kwargs: 透传self.client.request(..., **kwargs)中的kwargs
        :return : 含自定义指标的dict；key value形式。
        建议key值不要使用：request_type、response_time、name、context、response、exception、start_time、url，否则将会覆盖locust原生统计数据。
        """
        if not kwargs.get("stream"):
            return None
        first_flag = True
        result = dict()
        response_length = 0
        for ret in response.iter_lines(decode_unicode=False):
            if isinstance(ret, bytes):
                ret = ret.decode("utf-8")
            if ret:
                response_length += len(ret)
                if first_flag:
                    result["ttft"] = (
                        time.perf_counter() - start_time
                    ) * 1000  # 首Token延迟
                    first_flag = False
        result["response_length"] = response_length  # 会覆盖locust response_length统计
        result["request_length"] = (
            len(response.request.body) if response.request.body else 0
        )
        return result

    def check_response(
        self, response: ResponseContextManager
    ) -> ResponseContextManager:
        """
        校验返回，当catch_response=False (client.request默认行为)时执行此函数.
        标记成功（默认无需执行）：response.success()
        标记失败：response.failure(exc)
        """
        return response


class CustomHttpSession(HttpSession):
    """
    custom http session class
    """

    def __init__(
        self,
        base_url: str,
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
            base_url, request_event, user, *args, pool_manager=pool_manager, **kwargs
        )

    def request(  # type: ignore
        self,
        method: str,
        url: str,
        name: Optional[str] = None,
        catch_response: bool = False,
        context: Dict[str, Any] = {},
        **kwargs: Any
    ) -> requests.Response:
        """
        Constructs and sends a :py:class:`requests.Request`.
        Returns :py:class:`requests.Response` object.
        """
        # if group name has been set and no name parameter has been passed in;
        # set the name parameter to group_name
        if self.request_name and not name:
            name = self.request_name

        # prepend url with hostname unless it's already an absolute URL
        url = self._build_url(url)

        start_time = time.time()
        start_perf_counter = time.perf_counter()
        response = self._send_request_safe_mode(method, url, **kwargs)

        # yame自定义逻辑
        custom_result = self.user.set_result(response, start_perf_counter, **kwargs)
        ######################################

        response_time = (time.perf_counter() - start_perf_counter) * 1000

        request_before_redirect = (
            response.history and response.history[0] or response
        ).request
        url = request_before_redirect.url

        if not name:
            name = request_before_redirect.path_url

        if self.user:
            context = {**self.user.context(), **context}

        # store meta data that is used when reporting the request to locust's statistics
        request_meta = {
            "request_type": method,
            "response_time": response_time,
            "name": name,
            "context": context,
            "response": response,
            "exception": None,
            "start_time": start_time,
            "url": url,
        }

        # get the length of the content,
        # but if the argument stream is set to True, we take
        # the size from the content-length header,
        # in order to not trigger fetching of the body
        if kwargs.get("stream", False):
            # yame自定义逻辑
            if custom_result:  # request_meta添加自定义数据
                request_meta.update(custom_result)
            request_meta["response_length"] = request_meta.get(
                "response_length",  # 尝试优先读取自定义response_length
                int(response.headers.get("content-length") or 0),
            )
        else:
            request_meta["response_length"] = len(response.content or b"")

        if catch_response:
            return ResponseContextManager(
                response, request_event=self.request_event, request_meta=request_meta
            )
        else:
            with ResponseContextManager(
                response, request_event=self.request_event, request_meta=request_meta
            ) as rcm:
                self.user.check_response(
                    rcm
                )  # yame自定义逻辑，catch_response=False时执行.
            return response
