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

import hashlib
import json
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

from qianfan.config import Config, get_config
from qianfan.consts import Consts
from qianfan.errors import AuthError, InternalError, InvalidArgumentError
from qianfan.resources.http_client import HTTPClient
from qianfan.resources.typing import QfRequest, RetryConfig
from qianfan.utils import (
    AsyncLock,
    log_error,
    log_info,
    log_warn,
)


def _masked_ak(ak: str) -> str:
    """
    mask ak, only display first 6 characters
    """
    return ak[:6] + "***"


class AuthManager:
    """
    AuthManager is to manage all access token in SDK
    """

    class Token:
        """
        Token object
        """

        token: Optional[str]
        lock: threading.Lock
        alock: AsyncLock
        refresh_at: float
        expire_at: float
        refresh_func: Optional[Callable[..., Dict]]
        """
        custom refresh function
        return {
            "token": "",
            "expire_at": 0, # optional
            "refresh_at": 0, # optional
        }
        """

        def __init__(
            self,
            access_token: Optional[str] = None,
            refresh_at: float = 0,
            expire_at: float = 0,
            refresh_func: Optional[Callable[..., Dict]] = None,
        ):
            """
            Init access token object
            """
            self.token = access_token
            self.lock = threading.Lock()
            self.alock = AsyncLock()
            self.refresh_at = refresh_at
            self.expire_at = expire_at
            self.refresh_func = refresh_func

    _token_map: Dict[Tuple[str, str], Token]

    def __init__(self, **kwargs: Any) -> None:
        """
        Init Auth manager
        """
        self._token_map = {}
        self._client = HTTPClient()
        self._lock = threading.Lock()
        self._alock = AsyncLock()
        self.config = kwargs.get("config", get_config())

    def _register(
        self,
        ak: str,
        sk: str,
        access_token: Optional[str] = None,
        refresh_func: Optional[Callable[..., Dict]] = None,
    ) -> bool:
        """
        add `(ak, sk)` to manager and return whether provided `(ak, sk)` is existed
        this function is not thread safe !!!
        """
        existed = True

        if (ak, sk) not in self._token_map:
            self._token_map[(ak, sk)] = AuthManager.Token(
                access_token, refresh_func=refresh_func
            )
            existed = False
        else:
            # if user provide new access token for existed (ak, sk), update it
            if access_token is not None:
                self._token_map[(ak, sk)].token = access_token
                self._token_map[(ak, sk)].refresh_at = 0
        return existed

    def register(
        self,
        ak: str,
        sk: str,
        access_token: Optional[str] = None,
        refresh_func: Optional[Callable[..., Dict]] = None,
    ) -> None:
        """
        add `(ak, sk)` to manager and update access token
        """
        with self._lock:
            existed = self._register(ak, sk, access_token, refresh_func)

        if not existed and access_token is None:
            self.refresh_token(ak, sk)

    async def aregister(
        self,
        ak: str,
        sk: str,
        access_token: Optional[str] = None,
        refresh_func: Optional[Callable[..., Dict]] = None,
    ) -> None:
        """
        async add `(ak, sk)` to manager and update access token
        """
        async with self._alock:
            existed = self._register(ak, sk, access_token, refresh_func)

        if not existed and access_token is None:
            await self.arefresh_access_token(ak, sk)

    def _get_token_object(
        self, ak: str, sk: str
    ) -> Token:  # pylint:disable=undefined-variable
        """
        get token object by `(ak, sk)`
        this function is not thread safe !!!
        """
        obj = self._token_map.get((ak, sk), None)
        if obj is None:
            raise InternalError("provided ak and sk are not registered")
        return obj

    def _get_token_from_token_object(
        self, obj: Token, ak: str = "", sk: str = ""
    ) -> str:
        """
        get token from token object
        this function is not thread safe and should be protected by lock from obj !!!
        """
        if obj.token is None:
            log_warn(f"access token is not available for ak `{_masked_ak(ak)}`")
            return ""
        return obj.token

    def get_token(self, ak: str, sk: str) -> str:
        """
        get token by `(ak, sk)`
        """
        with self._lock:
            obj = self._get_token_object(ak, sk)
        # 提前刷新
        if obj.expire_at != 0 and obj.expire_at - 10 < time.time():
            self.refresh_token(ak, sk)
        with obj.lock:
            return self._get_token_from_token_object(obj, ak, sk)

    async def aget_token(self, ak: str, sk: str) -> str:
        """
        async get token by `(ak, sk)`
        """
        async with self._alock:
            obj = self._get_token_object(ak, sk)
        async with obj.alock:
            return self._get_token_from_token_object(obj, ak, sk)

    def _auth_request(self, ak: str, sk: str) -> QfRequest:
        """
        generate auth request
        """
        return QfRequest(
            method="POST",
            url="{}{}".format(self.config.BASE_URL, Consts.AuthAPI),
            query={
                "grant_type": "client_credentials",
                "client_id": ak,
                "client_secret": sk,
            },
            retry_config=RetryConfig(timeout=self.config.AUTH_TIMEOUT),
        )

    def _update_access_token(
        self, obj: Token, response: Dict[str, Any], ak: str = "", sk: str = ""
    ) -> None:
        """
        update access token from response of auth request
        this function is not thread safe and should be protected by lock from obj !!!
        """
        if "error" in response:
            error = response["error"]
            if error == "invalid_client":
                exception_msg_tmpl = (
                    "{err_msg}, please check! {chinese_err_msg}, 请检查！ AK/SK should"
                    " be obtained from"
                    " https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application"
                )
                err_msg = response.get("error_description", "AK/SK is not correct")
                chinese_err_msg = response.get("error_description", "AK/SK 错误")
                if err_msg == "unknown client id":
                    err_msg = f"AK({_masked_ak(ak)}) is not correct"
                    chinese_err_msg = f"AK(`{_masked_ak(ak)}`) 错误"
                if err_msg == "Client authentication failed":
                    err_msg = f"SK({_masked_ak(sk)}) is not correct"
                    chinese_err_msg = f"SK(`{_masked_ak(sk)}`) 错误"
                err_msg = exception_msg_tmpl.format(
                    err_msg=err_msg, chinese_err_msg=chinese_err_msg
                )
                log_error(err_msg)
                raise AuthError(err_msg)
            # unexpected error, maybe it can be recovered by retrying.
            log_error(
                "refresh access_token for ak `{}` failed, error description={}".format(
                    _masked_ak(ak), response["error_description"]
                )
            )
            return
        self._update_token(obj, response["access_token"])

    def _update_token(
        self,
        obj: Token,
        token: str,
        refresh_at: float = 0,
        expire_at: float = 0,
    ) -> None:
        obj.token = token
        obj.refresh_at = refresh_at or time.time()
        if expire_at != 0:
            obj.expire_at = expire_at

    def _is_refresh_token_too_often(self, obj: Token) -> bool:
        """
        check if token is refreshed too often
        """
        if (
            time.time() + 10 - obj.refresh_at  # 提前十秒刷新
            < self.config.ACCESS_TOKEN_REFRESH_MIN_INTERVAL
        ):
            log_info("token is already refreshed, skip refresh.")
            return True
        return False

    def refresh_token(self, ak: str, sk: str) -> None:
        with self._lock:
            obj = self._get_token_object(ak, sk)
        with obj.lock:
            log_info(f"trying to refresh token for ak `{_masked_ak(ak)}`")
            # in case multiple threads try to refresh access token at the same time
            # the token should not be refreshed multiple times
            if self._is_refresh_token_too_often(obj):
                return
            try:
                if obj.refresh_func:
                    # bearer token
                    token_resp = obj.refresh_func(ak, sk)
                    token = token_resp.get("token", "")
                    self._update_token(
                        obj,
                        token=token,
                        refresh_at=token_resp.get("refresh_at", 0),
                        expire_at=token_resp.get("expire_at", 0),
                    )
                else:
                    # access token
                    resp = self._client.request(self._auth_request(ak, sk))
                    json_body = resp.json()
                    self._update_access_token(obj, json_body, ak, sk)
            except AuthError:
                raise
            except Exception as e:
                log_error(f"refresh token failed with exception {str(e)}")
                raise e

        log_info("successfully refresh token")

    async def arefresh_access_token(self, ak: str, sk: str) -> None:
        """
        async refresh access token of `(ak, sk)`
        """
        async with self._alock:
            obj = self._get_token_object(ak, sk)
        async with obj.alock:
            log_info(f"trying to refresh access_token for ak `{_masked_ak(ak)}`")
            # in case multiple threads try to refresh access token at the same time
            # the token should not be refreshed multiple times
            if self._is_refresh_token_too_often(obj):
                return
            try:
                if obj.refresh_func:
                    # bearer token
                    # TODO: implement bearer token refresh async
                    token_resp = obj.refresh_func(ak, sk)
                    token = token_resp.get("token", "")
                    self._update_token(
                        obj,
                        token=token,
                        refresh_at=token_resp.get("refresh_at", 0),
                        expire_at=token_resp.get("expire_at", 0),
                    )
                else:
                    resp, session = await self._client.arequest(
                        self._auth_request(ak, sk)
                    )
                    async with session:
                        json_body = await resp.json()
                    self._update_access_token(obj, json_body, ak, sk)
            except AuthError:
                raise
            except Exception as e:
                log_error(f"refresh access token failed with exception {str(e)}")
                return

        log_info(f"sucessfully refresh access_token for ak `{_masked_ak(ak)}`")


class Auth(object):
    """
    object to maintain authorization info for open api call
    including access_token, ak/sk and access_key/secret_key
    """

    _ak: Optional[str] = None
    _sk: Optional[str] = None
    _access_token: Optional[str] = None
    _bearer_token: Optional[str] = None
    _access_key: Optional[str] = None
    _secret_key: Optional[str] = None
    _registered: bool = False
    _refresh_func: Optional[Callable[..., Dict]] = None
    _config: Optional[Config] = None

    def __init__(
        self, refresh_func: Optional[Callable[..., Dict]] = None, **kwargs: Any
    ) -> None:
        """
        recv `ak`, `sk` and `access_token` from kwargs
        if the args does not contain the arguments, env variable will be used

        when `ak` and `sk` are provided, `access_token` will be set automatically
        """
        self._config = kwargs.get("config", get_config())
        assert self._config
        if self._config.ENABLE_PRIVATE:
            return
        self._manager_lock = threading.Lock()
        self._ak = kwargs.get("ak", None) or self._config.AK
        self._sk = kwargs.get("sk", None) or self._config.SK
        self._access_token = (
            kwargs.get("access_token", None) or self._config.ACCESS_TOKEN
        )
        self._bearer_token = (
            kwargs.get("bearer_token", None) or self._config.BEARER_TOKEN
        )
        self._access_key = kwargs.get("access_key", None) or self._config.ACCESS_KEY
        self._secret_key = kwargs.get("secret_key", None) or self._config.SECRET_KEY
        self._refresh_func = refresh_func
        if not self._credential_available() and not self._config.NO_AUTH:
            raise InvalidArgumentError(
                "no enough credential found, use any one of (access_key, secret_key),"
                " (ak, sk), (access_token) in api v1 or"
                " any of (ak, sk), (bearer token) in api v2"
            )
        if (
            self._access_token is None
            and (self._ak is None or self._sk is None)
            and (
                self._access_key is not None
                and self._secret_key is not None
                and refresh_func is None
            )
        ):
            self._registered = True

    @property
    def _manager(self) -> AuthManager:
        with self._manager_lock:
            if not hasattr(self, "_auth_manager"):
                self._auth_manager = AuthManager(config=self._config)
        return self._auth_manager

    def _register(self) -> None:
        """
        register the access token to manager, so that it can be refreshed automatically
        """
        if not self._registered:
            if self._access_key and self._secret_key and self._refresh_func:
                # 注册bearer token
                self._manager.register(
                    self._access_key,
                    self._secret_key,
                    self._bearer_token,
                    self._refresh_func,
                )
            elif self._bearer_token is not None and self._refresh_func:
                self._registered = True
            elif self._access_token is None:
                # if access_token is not provided, both ak and sk should be provided
                if self._ak is None or self._sk is None:
                    raise InvalidArgumentError(
                        "both ak and sk must be provided, otherwise access_token should"
                        " be provided"
                    )
                self._manager.register(self._ak, self._sk, self._access_token)
            else:
                # if access_token is provided
                if not (self._ak is None or self._sk is None):
                    # only register to manager when both ak and sk are provided
                    self._manager.register(self._ak, self._sk, self._access_token)
            self._registered = True

    async def _aregister(self) -> None:
        """
        register the access token to manager, so that it can be refreshed automatically
        """
        if not self._registered:
            if self._access_key and self._secret_key and self._refresh_func:
                await self._manager.aregister(
                    self._access_key,
                    self._secret_key,
                    self._bearer_token,
                    self._refresh_func,
                )
            elif self._bearer_token is not None and self._refresh_func:
                self._registered = True
            if self._access_token is None:
                # if access_token is not provided, both ak and sk should be provided
                if self._ak is None or self._sk is None:
                    raise InvalidArgumentError(
                        "both ak and sk must be provided, otherwise access_token should"
                        " be provided"
                    )
                await self._manager.aregister(self._ak, self._sk, self._access_token)
            else:
                # if access_token is provided
                if not (self._ak is None or self._sk is None):
                    # only register to manager when both ak and sk are provided
                    await self._manager.aregister(
                        self._ak, self._sk, self._access_token
                    )
            self._registered = True

    def refresh_bearer_token(self) -> None:
        """
        refresh `bearer_token` using `access_key` and `secret_key`
        """
        if self._access_key is None or self._secret_key is None:
            log_warn(
                "access_key or secret_key is not set, refresh bearer_token will not"
                " work."
            )
            return
        self._register()
        self._manager.refresh_token(self._access_key, self._secret_key)
        self._bearer_token = None

    def refresh_access_token(self) -> None:
        """
        refresh `access_token` using `ak` and `sk`
        """
        if self._ak is None or self._sk is None:
            log_warn("AK or SK is not set, refresh access_token will not work.")
            return
        self._register()
        self._manager.refresh_token(self._ak, self._sk)
        self._access_token = None

    async def arefresh_access_token(self) -> None:
        """
        refresh `access_token` using `ak` and `sk`
        """
        if self._ak is None or self._sk is None:
            log_warn("AK or SK is not set, refresh access_token will not work.")
            return
        await self._aregister()
        await self._auth_manager.arefresh_access_token(self._ak, self._sk)
        self._access_token = None

    def _credential_available(self) -> bool:
        if self._refresh_func:
            if self._bearer_token is not None:
                return True
            elif self._access_key is not None and self._secret_key is not None:
                return True
            else:
                log_warn(
                    "no enough credential found, any one of (access_key, secret_key),"
                    " (bearer_token) must be provided"
                )
                return False
        if self._access_token is not None:
            return True
        if self._ak is not None and self._sk is not None:
            return True
        if self._access_key is not None and self._secret_key is not None:
            return True
        log_warn(
            "no enough credential found, any one of (access_key, secret_key),"
            " (ak, sk), (access_token) must be provided"
        )
        return False

    def credential_hash(self) -> str:
        sha256 = hashlib.sha256()

        sha256.update(
            json.dumps(
                [
                    self._access_token,
                    self._ak,
                    self._sk,
                    self._access_key,
                    self._secret_key,
                    self._bearer_token,
                ]
            ).encode("utf-8")
        )
        return sha256.hexdigest()

    def access_token(self) -> str:
        """
        get current `access_token`
        """
        if self._access_token is not None and (self._ak is None or self._sk is None):
            return self._access_token
        self._register()
        if self._ak is None or self._sk is None:
            # use access_key and secret_key to auth
            # so no access_token here
            return ""
        return self._manager.get_token(self._ak, self._sk)

    async def a_access_token(self) -> str:
        """
        get current `access_token`
        """
        if self._access_token is not None and (self._ak is None or self._sk is None):
            return self._access_token
        await self._aregister()
        if self._ak is None or self._sk is None:
            # use access_key and secret_key to auth
            # so no access_token here
            return ""
        return await self._manager.aget_token(self._ak, self._sk)

    def bearer_token(self) -> str:
        """
        get current `bearer_token`
        """
        if self._bearer_token is not None and (
            self._access_key is None or self._secret_key is None
        ):
            return self._bearer_token
        self._register()
        if self._access_key is not None and self._secret_key is not None:
            return self._manager.get_token(self._access_key, self._secret_key)
        return ""

    async def a_bearer_token(self) -> str:
        """
        async get current `bearer_token`
        """
        if self._bearer_token is not None and (
            self._access_key is None or self._secret_key is None
        ):
            return self._bearer_token
        await self._aregister()
        if self._access_key is not None and self._secret_key is not None:
            return await self._manager.aget_token(self._access_key, self._secret_key)
        return ""
