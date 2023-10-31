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
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import deprecated

from qianfan.consts import DefaultValue, Env


class GlobalConfig(BaseSettings):
    """
    The global config of whole qianfan sdk
    """

    model_config = SettingsConfigDict(env_prefix="QIANFAN_", case_sensitive=True)

    AK: Optional[str] = Field(default=None)
    SK: Optional[str] = Field(default=None)
    ACCESS_KEY: Optional[str] = Field(default=None)
    SECRET_KEY: Optional[str] = Field(default=None)
    ACCESS_TOKEN: Optional[str] = Field(default=None)
    BASE_URL: str = Field(default=DefaultValue.BaseURL)
    AUTH_TIMEOUT: float = Field(default=DefaultValue.AuthTimeout)
    DISABLE_EB_SDK: bool = Field(default=DefaultValue.DisableErnieBotSDK)
    EB_SDK_INSTALLED: bool = Field(default=False)
    IAM_SIGN_EXPIRATION_SEC: int = Field(default=DefaultValue.IAMSignExpirationSeconds)
    CONSOLE_API_BASE_URL: str = Field(default=DefaultValue.ConsoleAPIBaseURL)
    ACCESS_TOKEN_REFRESH_MIN_INTERVAL: float = Field(
        default=DefaultValue.AccessTokenRefreshMinInterval
    )
    QPS_LIMIT: float = Field(default=DefaultValue.QpsLimit)

    # for private
    ENABLE_PRIVATE: bool = Field(default=DefaultValue.EnablePrivate)
    # todo 补充 ENABLE_AUTH 的默认值和使用方法
    ENABLE_AUTH: Optional[bool] = Field(default=None)
    ACCESS_CODE: Optional[str] = Field(default=None)


_GLOBAL_CONFIG: Optional[GlobalConfig] = None


def get_config() -> GlobalConfig:
    global _GLOBAL_CONFIG
    if not _GLOBAL_CONFIG:
        try:
            _GLOBAL_CONFIG = GlobalConfig(  # type: ignore
                _env_file=os.getenv(Env.DotEnvConfigFile, DefaultValue.DotEnvConfigFile)
            )
        except Exception as e:
            # todo 解决引入 Logger 带来的循环引用问题
            # logger.error(f"unexpected error: {e}")
            raise e
    return _GLOBAL_CONFIG


@deprecated(
    "setting config via specific function is deprecated, please get config with"
    " get_config() and set attributes directly"
)
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
    get_config().AK = ak


@deprecated(
    "setting config via specific function is deprecated, please get config with"
    " get_config() and set attributes directly"
)
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
    get_config().SK = sk


@deprecated(
    "setting config via specific function is deprecated, please get config with"
    " get_config() and set attributes directly"
)
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
    get_config().ACCESS_TOKEN = access_token


@deprecated(
    "setting config via specific function is deprecated, please get config with"
    " get_config() and set attributes directly"
)
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
    get_config().ACCESS_KEY = access_key


@deprecated(
    "setting config via specific function is deprecated, please get config with"
    " get_config() and set attributes directly"
)
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
    get_config().SECRET_KEY = secret_key
