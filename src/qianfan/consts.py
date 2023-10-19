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

"""
Consts used in qianfan sdk
"""

import enum


class APIErrorCode(enum.Enum):
    """
    Error code from API return value
    """

    NoError = 0
    UnknownError = 1
    ServiceUnavailable = 2
    UnsupportedMethod = 3
    RequestLimitReached = 4
    NoPermissionToAccessData = 6
    GetServiceTokenFailed = 13
    AppNotExist = 15
    DailyLimitReached = 17
    QPSLimitReached = 18
    TotalRequestLimitReached = 19
    InvalidRequest = 100
    APITokenInvalid = 110
    APITokenExpired = 111
    InternalError = 336000
    InvalidArgument = 336001
    InvalidJSON = 336002
    InvalidParam = 336003
    PermissionError = 336004
    APINameNotExist = 336005
    ServerHighLoad = 336100
    InvalidHTTPMethod = 336101
    InvalidArgumentSystem = 336104
    InvalidArgumentUserSetting = 336105


class Env:
    """
    Environment variable name used by qianfan sdk
    """

    AK: str = "QIANFAN_AK"
    SK: str = "QIANFAN_SK"
    ConsoleAK: str = "QIANFAN_ACCESS_KEY"
    ConsoleSK: str = "QIANFAN_SECRET_KEY"
    AccessToken: str = "QIANFAN_ACCESS_TOKEN"
    BaseURL: str = "QIANFAN_BASE_URL"
    DisableErnieBotSDK: str = "QIANFAN_DISABLE_EB_SDK"
    AuthTimeout: str = "QIANFAN_AUTH_TIMEOUT"
    IAMSignExpirationSeconds: str = "QIANFAN_IAM_SIGN_EXPIRATION_SEC"
    ConsoleAPIBaseURL: str = "QIANFAN_CONSOLE_API_BASE_URL"
    AccessTokenRefreshMinInterval: str = "QIANFAN_ACCESS_TOKEN_REFRESH_MIN_INTERVAL"


class DefaultValue:
    """
    Default value used by qianfan sdk
    """

    AK: str = ""
    SK: str = ""
    ConsoleAK: str = ""
    ConsoleSK: str = ""
    AccessToken: str = ""
    BaseURL: str = "https://aip.baidubce.com"
    AuthTimeout: str = "5"
    DisableErnieBotSDK: str = "True"
    IAMSignExpirationSeconds: str = "300"
    ConsoleAPIBaseURL: str = "https://qianfan.baidubce.com"
    AccessTokenRefreshMinInterval: str = "3600"
    RetryCount: int = 1
    RetryTimeout: float = 60
    RetryBackoffFactor: float = 0


class Consts:
    """
    Constant used by qianfan sdk
    """

    ModelAPIPrefix: str = "/rpc/2.0/ai_custom/v1/wenxinworkshop"
    AuthAPI: str = "/oauth/2.0/token"
    FineTuneGetJobAPI: str = "/wenxinworkshop/finetune/jobDetail"
    FineTuneCreateTaskAPI: str = "/wenxinworkshop/finetune/createTask"
    FineTuneCreateJobAPI: str = "/wenxinworkshop/finetune/createJob"
    FineTuneStopJobAPI: str = "/wenxinworkshop/finetune/stopJob"
    ModelDetailAPI: str = "/wenxinworkshop/modelrepo/modelDetail"
    ModelVersionDetailAPI: str = "/wenxinworkshop/modelrepo/modelVersionDetail"
    ModelPublishAPI: str = "/wenxinworkshop/modelrepo/publishTrainModel"
    ServiceCreateAPI: str = "/wenxinworkshop/service/apply"
    ServiceDetailAPI: str = "/wenxinworkshop/service/detail"
    STREAM_RESPONSE_PREFIX: str = "data: "


class DefaultLLMModel:
    """
    Defualt LLM model in qianfan sdk
    """

    Completion = "ERNIE-Bot-turbo"
    ChatCompletion = "ERNIE-Bot-turbo"
    Embedding = "Embedding-V1"
