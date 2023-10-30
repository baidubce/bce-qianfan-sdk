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
import os
import sys
import typing
from importlib.util import find_spec
from typing import Any, Callable, Optional

from qianfan.consts import DefaultValue, Env
from qianfan.errors import InvalidArgumentError
from qianfan.utils import _get_from_env_or_default, _none_if_empty, _strtobool, log_info
from qianfan.utils.helper import Singleton


class GlobalConfig(object, metaclass=Singleton):
    """
    The global config of whole qianfan sdk
    """

    AK: Optional[str]
    SK: Optional[str]
    CONSOLE_AK: Optional[str]
    CONSOLE_SK: Optional[str]
    ACCESS_TOKEN: Optional[str]
    BASE_URL: str
    AUTH_TIMEOUT: float
    DISABLE_EB_SDK: bool
    EB_SDK_INSTALLED: bool
    IAM_SIGN_EXPIRATION_SEC: int
    CONSOLE_API_BASE_URL: str
    ACCESS_TOKEN_REFRESH_MIN_INTERVAL: float
    QPS_LIMIT: float

    def __init__(self) -> None:
        """
        Read value from environment or the default value will be used
        """
        try:
            self.BASE_URL = _get_from_env_or_default(Env.BaseURL, DefaultValue.BaseURL)
            self.AUTH_TIMEOUT = float(
                _get_from_env_or_default(Env.AuthTimeout, DefaultValue.AuthTimeout)
            )
            self.DISABLE_EB_SDK = _strtobool(
                _get_from_env_or_default(
                    Env.DisableErnieBotSDK, DefaultValue.DisableErnieBotSDK
                )
            )
            self.AK = _none_if_empty(_get_from_env_or_default(Env.AK, DefaultValue.AK))
            self.SK = _none_if_empty(_get_from_env_or_default(Env.SK, DefaultValue.SK))
            self.ACCESS_TOKEN = _none_if_empty(
                _get_from_env_or_default(Env.AccessToken, DefaultValue.AccessToken)
            )
            self.CONSOLE_AK = _none_if_empty(
                _get_from_env_or_default(Env.ConsoleAK, DefaultValue.ConsoleAK)
            )
            self.CONSOLE_SK = _none_if_empty(
                _get_from_env_or_default(Env.ConsoleSK, DefaultValue.ConsoleSK)
            )
            self.IAM_SIGN_EXPIRATION_SEC = int(
                _get_from_env_or_default(
                    Env.IAMSignExpirationSeconds, DefaultValue.IAMSignExpirationSeconds
                )
            )
            self.CONSOLE_API_BASE_URL = _get_from_env_or_default(
                Env.ConsoleAPIBaseURL, DefaultValue.ConsoleAPIBaseURL
            )
            self.ACCESS_TOKEN_REFRESH_MIN_INTERVAL = float(
                _get_from_env_or_default(
                    Env.AccessTokenRefreshMinInterval,
                    DefaultValue.AccessTokenRefreshMinInterval,
                )
            )
            self.QPS_LIMIT = float(
                _get_from_env_or_default(Env.QpsLimit, DefaultValue.QpsLimit)
            )
        except Exception as e:
            raise InvalidArgumentError(
                f"Got invalid envrionment variable with err `{str(e)}`"
            )
        self.EB_SDK_INSTALLED = True
        if find_spec("erniebot") is None:
            log_info(
                "erniebot is not installed, all operations will fall back to qianfan"
                " sdk."
            )
            self.EB_SDK_INSTALLED = False


GLOBAL_CONFIG = GlobalConfig()


def _os_environ_set_hook(func: Callable) -> Callable:
    def inner(key: Any, value: Any) -> None:
        decoded_key = os.environ.decodekey(key)
        decoded_val = os.environ.decodevalue(value)
        if decoded_key in Env.__dict__.values():
            attrs = decoded_key[8:]
            base_t = GlobalConfig.__annotations__[attrs]
            typing_t = (
                base_t.__args__
                if isinstance(base_t, typing._GenericAlias)  # type: ignore
                else None  # type: ignore
            )
            if typing_t:
                setattr(GLOBAL_CONFIG, attrs, (typing_t[0])(decoded_val))
            else:
                if base_t == bool:
                    setattr(GLOBAL_CONFIG, attrs, _strtobool(decoded_val))
                else:
                    setattr(GLOBAL_CONFIG, attrs, base_t(decoded_val))
        func(key, value)

    return inner


if sys.version_info >= (3, 9):
    os.putenv = _os_environ_set_hook(os.putenv)
else:
    os.environ.putenv = _os_environ_set_hook(os.environ.putenv)


def _os_environ_del_hook(func: Callable) -> Callable:
    def inner(key: Any) -> None:
        decoded_key = os.environ.decodekey(key)
        for k, v in vars(Env).items():
            if decoded_key == v:
                attrs = decoded_key[8:]
                base_t = GlobalConfig.__annotations__[attrs]
                typing_t = (
                    base_t.__args__
                    if isinstance(base_t, typing._GenericAlias)  # type: ignore
                    else None  # type: ignore
                )
                if typing_t and type(None) in typing_t:
                    setattr(GLOBAL_CONFIG, attrs, None)
                else:
                    default_val = DefaultValue.__dict__[k]
                    setattr(GLOBAL_CONFIG, attrs, base_t(default_val))
                break
        func(key)

    return inner


if sys.version_info >= (3, 9):
    os.unsetenv = _os_environ_del_hook(os.unsetenv)
else:
    os.environ.unsetenv = _os_environ_del_hook(os.environ.unsetenv)


def AK(ak: str) -> None:
    """
    Set the API Key (AK) for LLM API authentication.

    This function allows you to set the API Key that will be used for authentication
    throughout the entire SDK. The API Key can be acquired from the qianfan console:
    https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application

    Parameters:
      ak (str):
        The API Key to be set for LLM API authentication.
    """
    GLOBAL_CONFIG.AK = ak


def SK(sk: str) -> None:
    """
    Set the Secret Key (SK) for LLM api authentication. The secret key is paired with
    the API key.

    This function allows you to set the Secret Key that will be used for authentication
    throughout the entire SDK. The Secret Key can be acquired from the qianfan console:
    https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application

    Parameters:
      sk (str):
        The Secret Key to be set for LLM API authentication.
    """
    GLOBAL_CONFIG.SK = sk


def AccessToken(access_token: str) -> None:
    """
    Set the access token for LLM api authentication.

    This function allows you to set the access token that will be used for
    authentication throughout the entire SDK. The access token can be generated from
    API key and secret key according to the instructions at
    https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Ilkkrb0i5.

    This function is only needed when you only have access token. If you have both API
    key and secret key, sdk will automatically refresh the access token for you.

    Parameters:
      access_token (str):
        The access token to be set for LLM API authentication.
    """
    GLOBAL_CONFIG.ACCESS_TOKEN = access_token


def AccessKey(access_key: str) -> None:
    """
    Set the Access Key for console api authentication.

    This function allows you to set the Access Key that will be used for
    authentication throughout the entire SDK. The Access Key can be acquired from
    the baidu bce console:
    https://console.bce.baidu.com/iam/#/iam/accesslist

    Parameters:
      access_key (str):
        The Access Key to be set for console API authentication.
    """
    GLOBAL_CONFIG.CONSOLE_AK = access_key


def SecretKey(secret_key: str) -> None:
    """
    Set the Secret Key for console api authentication. The secret key is paired with the
    access key.

    This function allows you to set the Secret Key that will be used for authentication
    throughout the entire SDK. The secret Key can be acquired from the baidu bce
    console:
    https://console.bce.baidu.com/iam/#/iam/accesslist

    Parameters:
      secret_key (str):
        The Secret Key to be set for console API authentication.
    """
    GLOBAL_CONFIG.CONSOLE_SK = secret_key
