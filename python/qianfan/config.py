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

from typing_extensions import deprecated

from qianfan.consts import DefaultValue, Env
from qianfan.utils.pydantic import BaseSettings, Field


class GlobalConfig(BaseSettings):
    """
    The global config of whole qianfan sdk
    """

    class Config:
        env_file_encoding = "utf-8"
        env_prefix = "QIANFAN_"
        case_sensitive = True

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
    RPM_LIMIT: float = Field(default=DefaultValue.RpmLimit)
    TPM_LIMIT: int = Field(default=DefaultValue.TpmLimit)
    APPID: Optional[int] = Field(default=None)

    # for private
    ENABLE_PRIVATE: bool = Field(default=DefaultValue.EnablePrivate)
    ENABLE_AUTH: Optional[bool] = Field(default=None)
    ACCESS_CODE: Optional[str] = Field(default=None)
    IMPORT_STATUS_POLLING_INTERVAL: float = Field(
        default=DefaultValue.ImportStatusPollingInterval
    )
    EXPORT_STATUS_POLLING_INTERVAL: float = Field(
        default=DefaultValue.ExportStatusPollingInterval
    )
    RELEASE_STATUS_POLLING_INTERVAL: float = Field(
        default=DefaultValue.ReleaseStatusPollingInterval
    )
    EXPORT_FILE_SIZE_LIMIT: int = Field(default=DefaultValue.ExportFileSizeLimit)
    ETL_STATUS_POLLING_INTERVAL: float = Field(
        default=DefaultValue.ETLStatusPollingInterval
    )
    GET_ENTITY_CONTENT_FAILED_RETRY_TIMES: int = Field(
        default=DefaultValue.GetEntityContentFailedRetryTimes
    )
    TRAIN_STATUS_POLLING_INTERVAL: float = Field(
        default=DefaultValue.TrainStatusPollingInterval
    )
    TRAINER_STATUS_POLLING_BACKOFF_FACTOR: float = Field(
        default=DefaultValue.TrainerStatusPollingBackoffFactor
    )
    TRAINER_STATUS_POLLING_RETRY_TIMES: float = Field(
        default=DefaultValue.TrainerStatusPollingRetryTimes
    )
    MODEL_PUBLISH_STATUS_POLLING_INTERVAL: float = Field(
        default=DefaultValue.ModelPublishStatusPollingInterval
    )
    BATCH_RUN_STATUS_POLLING_INTERVAL: float = Field(
        default=DefaultValue.BatchRunStatusPollingInterval
    )
    DEPLOY_STATUS_POLLING_INTERVAL: float = Field(
        default=DefaultValue.DeployStatusPollingInterval
    )
    DEFAULT_FINE_TUNE_TRAIN_TYPE: str = Field(
        default=DefaultValue.DefaultFinetuneTrainType
    )
    LLM_API_RETRY_COUNT: int = Field(default=DefaultValue.RetryCount)
    LLM_API_RETRY_TIMEOUT: int = Field(default=DefaultValue.RetryTimeout)
    LLM_API_RETRY_BACKOFF_FACTOR: float = Field(default=DefaultValue.RetryBackoffFactor)
    LLM_API_RETRY_JITTER: float = Field(default=DefaultValue.RetryJitter)
    LLM_API_RETRY_MAX_WAIT_INTERVAL: float = Field(
        default=DefaultValue.RetryMaxWaitInterval
    )
    LLM_API_RETRY_ERR_CODES: set = Field(default=DefaultValue.RetryErrCodes)
    CONSOLE_API_RETRY_COUNT: int = Field(default=DefaultValue.ConsoleRetryCount)
    CONSOLE_API_RETRY_TIMEOUT: int = Field(default=DefaultValue.ConsoleRetryTimeout)
    CONSOLE_API_RETRY_JITTER: float = Field(default=DefaultValue.ConsoleRetryJitter)
    CONSOLE_API_RETRY_MAX_WAIT_INTERVAL: float = Field(
        default=DefaultValue.ConsoleRetryMaxWaitInterval
    )
    CONSOLE_API_RETRY_ERR_CODES: set = Field(default=DefaultValue.ConsoleRetryErrCodes)
    CONSOLE_API_RETRY_BACKOFF_FACTOR: int = Field(
        default=DefaultValue.ConsoleRetryBackoffFactor
    )
    EVALUATION_ONLINE_POLLING_INTERVAL: float = Field(
        default=DefaultValue.EvaluationOnlinePollingInterval
    )
    BOS_HOST_REGION: str = Field(default=DefaultValue.BosHostRegion)

    # Warning
    # 这个配置项会关闭 SSL 证书校验功能，可能会导致潜在的不安全访问
    # 请勿在公共网络上关闭这一配置。由于关闭带来的一切问题，本项目均不负责
    SSL_VERIFICATION_ENABLED: bool = Field(default=DefaultValue.SSLVerificationEnabled)
    PROXY: str = Field(default=DefaultValue.Proxy)

    FILE_ENCODING: str = Field(default=DefaultValue.FileEncoding)


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


def encoding() -> str:
    """
    Get the file encoding used in the SDK.
    """
    return get_config().FILE_ENCODING
