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
from typing import Optional

from dynaconf import Dynaconf, Validator
from typing_extensions import deprecated

from qianfan.consts import DefaultValue

_GLOBAL_CONFIG: Optional[Dynaconf] = None


def get_config() -> Dynaconf:
    global _GLOBAL_CONFIG
    if not _GLOBAL_CONFIG:
        try:
            _none_default_value_key_list = [
                "AK",
                "SK",
                "ACCESS_KEY",
                "SECRET_KEY",
                "ACCESS_TOKEN",
                "APPID",
                "ENABLE_AUTH",
                "ACCESS_CODE",
            ]

            _GLOBAL_CONFIG = Dynaconf(
                validators=[
                    Validator(*_none_default_value_key_list, default=None),
                    Validator("BASE_URL", default=DefaultValue.BaseURL),
                    Validator("AUTH_TIMEOUT", default=DefaultValue.AuthTimeout),
                    Validator(
                        "DISABLE_EB_SDK", default=DefaultValue.DisableErnieBotSDK
                    ),
                    Validator("EB_SDK_INSTALLED", default=False),
                    Validator(
                        "IAM_SIGN_EXPIRATION_SEC",
                        default=DefaultValue.IAMSignExpirationSeconds,
                    ),
                    Validator(
                        "CONSOLE_API_BASE_URL", default=DefaultValue.ConsoleAPIBaseURL
                    ),
                    Validator(
                        "ACCESS_TOKEN_REFRESH_MIN_INTERVAL",
                        default=DefaultValue.AccessTokenRefreshMinInterval,
                    ),
                    Validator("QPS_LIMIT", default=DefaultValue.QpsLimit),
                    Validator("ENABLE_PRIVATE", default=DefaultValue.EnablePrivate),
                    Validator(
                        "IMPORT_STATUS_POLLING_INTERVAL",
                        default=DefaultValue.ImportStatusPollingInterval,
                    ),
                    Validator(
                        "EXPORT_STATUS_POLLING_INTERVAL",
                        default=DefaultValue.ExportStatusPollingInterval,
                    ),
                    Validator(
                        "RELEASE_STATUS_POLLING_INTERVAL",
                        default=DefaultValue.ReleaseStatusPollingInterval,
                    ),
                    Validator(
                        "EXPORT_FILE_SIZE_LIMIT",
                        default=DefaultValue.ExportFileSizeLimit,
                    ),
                    Validator(
                        "ETL_STATUS_POLLING_INTERVAL",
                        default=DefaultValue.ETLStatusPollingInterval,
                    ),
                    Validator(
                        "GET_ENTITY_CONTENT_FAILED_RETRY_TIMES",
                        default=DefaultValue.GetEntityContentFailedRetryTimes,
                    ),
                    Validator(
                        "TRAIN_STATUS_POLLING_INTERVAL",
                        default=DefaultValue.TrainStatusPollingInterval,
                    ),
                    Validator(
                        "TRAINER_STATUS_POLLING_BACKOFF_FACTOR",
                        default=DefaultValue.TrainerStatusPollingBackoffFactor,
                    ),
                    Validator(
                        "TRAINER_STATUS_POLLING_RETRY_TIMES",
                        default=DefaultValue.TrainerStatusPollingRetryTimes,
                    ),
                    Validator(
                        "MODEL_PUBLISH_STATUS_POLLING_INTERVAL",
                        default=DefaultValue.ModelPublishStatusPollingInterval,
                    ),
                    Validator(
                        "BATCH_RUN_STATUS_POLLING_INTERVAL",
                        default=DefaultValue.BatchRunStatusPollingInterval,
                    ),
                    Validator(
                        "DEPLOY_STATUS_POLLING_INTERVAL",
                        default=DefaultValue.DeployStatusPollingInterval,
                    ),
                    Validator(
                        "DEFAULT_FINE_TUNE_TRAIN_TYPE",
                        default=DefaultValue.DefaultFinetuneTrainType,
                    ),
                    Validator("LLM_API_RETRY_COUNT", default=DefaultValue.RetryCount),
                    Validator(
                        "LLM_API_RETRY_TIMEOUT", default=DefaultValue.RetryTimeout
                    ),
                    Validator(
                        "LLM_API_RETRY_BACKOFF_FACTOR",
                        default=DefaultValue.RetryBackoffFactor,
                    ),
                    Validator("LLM_API_RETRY_JITTER", default=DefaultValue.RetryJitter),
                    Validator(
                        "LLM_API_RETRY_ERR_CODES", default=DefaultValue.RetryErrCodes
                    ),
                    Validator(
                        "CONSOLE_API_RETRY_COUNT",
                        default=DefaultValue.ConsoleRetryCount,
                    ),
                    Validator(
                        "CONSOLE_API_RETRY_TIMEOUT",
                        default=DefaultValue.ConsoleRetryTimeout,
                    ),
                    Validator(
                        "CONSOLE_API_RETRY_JITTER",
                        default=DefaultValue.ConsoleRetryJitter,
                    ),
                    Validator(
                        "CONSOLE_API_RETRY_ERR_CODES",
                        default=DefaultValue.ConsoleRetryErrCodes,
                    ),
                    Validator(
                        "CONSOLE_API_RETRY_BACKOFF_FACTOR",
                        default=DefaultValue.ConsoleRetryBackoffFactor,
                    ),
                    Validator(
                        "EVALUATION_ONLINE_POLLING_INTERVAL",
                        default=DefaultValue.EvaluationOnlinePollingInterval,
                    ),
                    Validator("BOS_HOST_REGION", default=DefaultValue.BosHostRegion),
                ],
                load_dotenv=True,
                envvar_prefix="QIANFAN",
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
