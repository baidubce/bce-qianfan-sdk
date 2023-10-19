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

from importlib.util import find_spec
from typing import Optional

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
