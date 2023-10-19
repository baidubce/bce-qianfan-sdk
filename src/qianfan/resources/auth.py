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

import asyncio
import threading
import time
from typing import Any, Dict, Optional, Tuple

from baidubce.auth.bce_credentials import BceCredentials
from baidubce.auth.bce_v1_signer import sign
from baidubce.utils import get_canonical_time

from qianfan.config import GLOBAL_CONFIG
from qianfan.consts import Consts, Env
from qianfan.errors import InternalError, InvalidArgumentError
from qianfan.resources.http_client import HTTPClient
from qianfan.resources.typing import QfRequest, RetryConfig
from qianfan.utils import (
    _get_value_from_dict_or_var_or_env,
    log_error,
    log_info,
    log_warn,
)
from qianfan.utils.helper import Singleton


def _masked_ak(ak: str) -> str:
    """
    mask ak, only display first 6 characters
    """
    return ak[:6] + "***"


class AuthManager(metaclass=Singleton):
    """
    AuthManager is singleton to manage all access token in SDK
    """

    class AccessToken:
        """
        Access Token object
        """

        token: Optional[str]
        lock: threading.Lock
        alock: asyncio.Lock
        refresh_at: float

        def __init__(self, access_token: Optional[str] = None):
            """
            Init access token object
            """
            self.token = access_token
            self.lock = threading.Lock()
            self.alock = asyncio.Lock()
            self.refresh_at = 0

    _token_map: Dict[Tuple[str, str], AccessToken]

    def __init__(self) -> None:
        """
        Init Auth manager
        """
        self._token_map = {}
        self._client = HTTPClient()
        self._lock = threading.Lock()
        self._alock = asyncio.Lock()

    def _register(self, ak: str, sk: str, access_token: Optional[str] = None) -> bool:
        """
        add `(ak, sk)` to manager and return whether provided `(ak, sk)` is existed
        this function is not thread safe !!!
        """
        existed = True

        if (ak, sk) not in self._token_map:
            self._token_map[(ak, sk)] = AuthManager.AccessToken(access_token)
            existed = False
        else:
            # if user provide new access token for existed (ak, sk), update it
            if access_token is not None:
                self._token_map[(ak, sk)].token = access_token
                self._token_map[(ak, sk)].refresh_at = 0
        return existed

    def register(self, ak: str, sk: str, access_token: Optional[str] = None) -> None:
        """
        add `(ak, sk)` to manager and update access token
        """
        with self._lock:
            existed = self._register(ak, sk, access_token)

        if not existed and access_token is None:
            self.refresh_access_token(ak, sk)

    async def aregister(
        self, ak: str, sk: str, access_token: Optional[str] = None
    ) -> None:
        """
        async add `(ak, sk)` to manager and update access token
        """
        async with self._alock:
            existed = self._register(ak, sk, access_token)

        if not existed and access_token is None:
            await self.arefresh_access_token(ak, sk)

    def _get_access_token_object(
        self, ak: str, sk: str
    ) -> AccessToken:  # pylint:disable=undefined-variable
        """
        get access token object by `(ak, sk)`
        this function is not thread safe !!!
        """
        obj = self._token_map.get((ak, sk), None)
        if obj is None:
            raise InternalError("provided ak and sk are not registered")
        return obj

    def _get_token_from_access_token_object(
        self, obj: AccessToken, ak: str = "", sk: str = ""
    ) -> str:
        """
        get access token from access token object
        this function is not thread safe and should be protected by lock from obj !!!
        """
        if obj.token is None:
            log_warn(f"access token is not available for ak `{_masked_ak(ak)}`")
            return ""
        return obj.token

    def get_access_token(self, ak: str, sk: str) -> str:
        """
        get access token by `(ak, sk)`
        """
        with self._lock:
            obj = self._get_access_token_object(ak, sk)
        with obj.lock:
            return self._get_token_from_access_token_object(obj, ak, sk)

    async def aget_access_token(self, ak: str, sk: str) -> str:
        """
        async get access token by `(ak, sk)`
        """
        async with self._alock:
            obj = self._get_access_token_object(ak, sk)
        async with obj.alock:
            return self._get_token_from_access_token_object(obj, ak, sk)

    def _auth_request(self, ak: str, sk: str) -> QfRequest:
        """
        generate auth request
        """
        return QfRequest(
            method="POST",
            url="{}{}".format(GLOBAL_CONFIG.BASE_URL, Consts.AuthAPI),
            query={
                "grant_type": "client_credentials",
                "client_id": ak,
                "client_secret": sk,
            },
            retry_config=RetryConfig(timeout=GLOBAL_CONFIG.AUTH_TIMEOUT),
        )

    def _update_access_token(
        self, obj: AccessToken, response: Dict[str, Any], ak: str = "", sk: str = ""
    ) -> None:
        """
        update access token from response of auth request
        this function is not thread safe and should be protected by lock from obj !!!
        """
        if "error" in response:
            log_error(
                "refresh access_token for ak `{}` failed, error description={}".format(
                    _masked_ak(ak), response["error_description"]
                )
            )
            return
        obj.token = response["access_token"]
        obj.refresh_at = time.time()

    def _refresh_access_token_too_often(self, obj: AccessToken) -> bool:
        """
        check if access token is refreshed too often
        """
        if (
            time.time() - obj.refresh_at
            < GLOBAL_CONFIG.ACCESS_TOKEN_REFRESH_MIN_INTERVAL
        ):
            log_info("access_token is already refreshed, skip refresh.")
            return True
        return False

    def refresh_access_token(self, ak: str, sk: str) -> None:
        """
        refresh access token of `(ak, sk)`
        """
        with self._lock:
            obj = self._get_access_token_object(ak, sk)
        with obj.lock:
            log_info(f"trying to refresh access_token for ak `{_masked_ak(ak)}`")
            # in case multiple threads try to refresh access token at the same time
            # the token should not be refreshed multiple times
            if self._refresh_access_token_too_often(obj):
                return
            try:
                resp = self._client.request(self._auth_request(ak, sk))
                json_body = resp.json()
                self._update_access_token(obj, json_body, ak, sk)
            except Exception as e:
                log_error(f"refresh access token failed with exception {str(e)}")
                return

        log_info("sucessfully refresh access_token")

    async def arefresh_access_token(self, ak: str, sk: str) -> None:
        """
        async refresh access token of `(ak, sk)`
        """
        async with self._alock:
            obj = self._get_access_token_object(ak, sk)
        async with obj.alock:
            log_info(f"trying to refresh access_token for ak `{_masked_ak(ak)}`")
            # in case multiple threads try to refresh access token at the same time
            # the token should not be refreshed multiple times
            if self._refresh_access_token_too_often(obj):
                return
            try:
                resp, session = await self._client.arequest(self._auth_request(ak, sk))
                async with session:
                    json_body = await resp.json()
                self._update_access_token(obj, json_body, ak, sk)
            except Exception as e:
                log_error(f"refresh access token failed with exception {str(e)}")
                return

        log_info(f"sucessfully refresh access_token for ak `{_masked_ak(ak)}`")


class Auth(object):
    """
    object to maintain acccess token for api call
    """

    _ak: Optional[str] = None
    _sk: Optional[str] = None
    _access_token: Optional[str] = None
    _registered: bool = False

    def __init__(self, **kwargs: Any) -> None:
        """
        recv `ak`, `sk` and `access_token` from kwargs
        if the args does not contain the arguments, env variable will be used

        when `ak` and `sk` are provided, `access_token` will be set automatically
        """
        self._ak = _get_value_from_dict_or_var_or_env(
            kwargs, "ak", GLOBAL_CONFIG.AK, Env.AK
        )
        self._sk = _get_value_from_dict_or_var_or_env(
            kwargs, "sk", GLOBAL_CONFIG.SK, Env.SK
        )
        self._access_token = _get_value_from_dict_or_var_or_env(
            kwargs, "access_token", GLOBAL_CONFIG.ACCESS_TOKEN, Env.AccessToken
        )

    def _register(self) -> None:
        """
        register the access token to manager, so that it can be refreshed automatically
        """
        if not self._registered:
            if self._access_token is None:
                # if access_token is not provided, both ak and sk should be provided
                if self._ak is None or self._sk is None:
                    raise InvalidArgumentError(
                        "both ak and sk must be provided, otherwise access_token should"
                        " be provided"
                    )
                AuthManager().register(self._ak, self._sk, self._access_token)
            else:
                # if access_token is provided
                if not (self._ak is None or self._sk is None):
                    # only register to manager when both ak and sk are provided
                    AuthManager().register(self._ak, self._sk, self._access_token)
            self._registered = True

    async def _aregister(self) -> None:
        """
        register the access token to manager, so that it can be refreshed automatically
        """
        if not self._registered:
            if self._access_token is None:
                # if access_token is not provided, both ak and sk should be provided
                if self._ak is None or self._sk is None:
                    raise InvalidArgumentError(
                        "both ak and sk must be provided, otherwise access_token should"
                        " be provided"
                    )
                await AuthManager().aregister(self._ak, self._sk, self._access_token)
            else:
                # if access_token is provided
                if not (self._ak is None or self._sk is None):
                    # only register to manager when both ak and sk are provided
                    await AuthManager().aregister(
                        self._ak, self._sk, self._access_token
                    )
            self._registered = True

    def refresh_access_token(self) -> None:
        """
        refresh `access_token` using `ak` and `sk`
        """
        if self._ak is None or self._sk is None:
            log_warn("AK or SK is not set, refresh access_token will not work.")
            return
        self._register()
        AuthManager().refresh_access_token(self._ak, self._sk)

    async def arefresh_access_token(self) -> None:
        """
        refresh `access_token` using `ak` and `sk`
        """
        if self._ak is None or self._sk is None:
            log_warn("AK or SK is not set, refresh access_token will not work.")
            return
        await self._aregister()
        await AuthManager().arefresh_access_token(self._ak, self._sk)

    def access_token(self) -> str:
        """
        get current `access_token`
        """
        if self._ak is None or self._sk is None:
            if self._access_token is None:
                log_warn("Access token is not available! Please check code!")
                return ""
            return self._access_token
        self._register()
        return AuthManager().get_access_token(self._ak, self._sk)

    async def a_access_token(self) -> str:
        """
        get current `access_token`
        """
        if self._ak is None or self._sk is None:
            if self._access_token is None:
                log_warn("Access token is not available! Please check code!")
                return ""
            return self._access_token
        await self._aregister()
        return await AuthManager().aget_access_token(self._ak, self._sk)


def iam_sign(
    ak: str,
    sk: str,
    request: QfRequest,
) -> None:
    """
    Create the authorization
    """
    credentials = BceCredentials(ak, sk)
    timestamp = time.time()
    x_bce_date = get_canonical_time(timestamp)
    request.headers["x-bce-date"] = x_bce_date
    authorization = sign(
        credentials,
        str.encode(request.method),
        str.encode(request.url),
        {str.encode(k): v for k, v in request.headers.items()},
        {str.encode(k): v for k, v in request.query.items()},
        timestamp=timestamp,
        expiration_in_seconds=GLOBAL_CONFIG.IAM_SIGN_EXPIRATION_SEC,
        headers_to_sign={str.encode(k.lower()) for k in request.headers.keys()},
    )

    request.headers["Authorization"] = authorization
