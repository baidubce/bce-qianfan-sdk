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
from typing import Set

from qianfan.version import VERSION


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
    RPMLimitReached = 336501
    TPMLimitReached = 336502

    ConsoleInternalError = 500000


class Env:
    """
    Environment variable name used by qianfan sdk
    """

    AK: str = "QIANFAN_AK"
    SK: str = "QIANFAN_SK"
    AccessKey: str = "QIANFAN_ACCESS_KEY"
    SecretKey: str = "QIANFAN_SECRET_KEY"
    AccessToken: str = "QIANFAN_ACCESS_TOKEN"
    BaseURL: str = "QIANFAN_BASE_URL"
    DisableErnieBotSDK: str = "QIANFAN_DISABLE_EB_SDK"
    AuthTimeout: str = "QIANFAN_AUTH_TIMEOUT"
    IAMSignExpirationSeconds: str = "QIANFAN_IAM_SIGN_EXPIRATION_SEC"
    ConsoleAPIBaseURL: str = "QIANFAN_CONSOLE_API_BASE_URL"
    AccessTokenRefreshMinInterval: str = "QIANFAN_ACCESS_TOKEN_REFRESH_MIN_INTERVAL"
    EnablePrivate: str = "QIANFAN_ENABLE_PRIVATE"
    AccessCode: str = "QIANFAN_PRIVATE_ACCESS_CODE"
    QpsLimit: str = "QIANFAN_QPS_LIMIT"
    RpmLimit: str = "QIANFAN_RPM_LIMIT"
    TpmLimit: str = "QIANFAN_TPM_LIMIT"
    DotEnvConfigFile: str = "QIANFAN_DOT_ENV_CONFIG_FILE"
    ImportStatusPollingInterval: str = "QIANFAN_IMPORT_STATUS_POLLING_INTERVAL"
    ExportStatusPollingInterval: str = "QIANFAN_EXPORT_STATUS_POLLING_INTERVAL"
    ReleaseStatusPollingInterval: str = "QIANFAN_RELEASE_STATUS_POLLING_INTERVAL"
    ExportFileSizeLimit: str = "QIANFAN_EXPORT_FILE_SIZE_LIMIT"
    ETLStatusPollingInterval: str = "QIANFAN_ETL_STATUS_POLLING_INTERVAL"
    GetEntityContentFailedRetryTimes: str = (
        "QIANFAN_GET_ENTITY_CONTENT_FAILED_RETRY_TIMES"
    )
    RetryCount: str = "QIANFAN_LLM_API_RETRY_COUNT"
    RetryTimeout: str = "QIANFAN_LLM_API_RETRY_TIMEOUT"
    RetryBackoffFactor: str = "QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR"
    ConsoleRetryCount: str = "QIANFAN_CONSOLE_API_RETRY_COUNT"
    ConsoleRetryTimeout: str = "QIANFAN_CONSOLE_API_RETRY_TIMEOUT"
    ConsoleRetryBackoffFactor: str = "QIANFAN_CONSOLE_API_RETRY_BACKOFF_FACTOR"

    SSLVerificationEnabled: str = "QIANFAN_SSL_VERIFICATION_ENABLED"
    Proxy: str = "QIANFAN_PROXY"
    FileEncoding: str = "QIANFAN_FILE_ENCODING"


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
    AuthTimeout: float = 5
    DisableErnieBotSDK: bool = True
    IAMSignExpirationSeconds: int = 300
    ConsoleAPIBaseURL: str = "https://qianfan.baidubce.com"
    AccessTokenRefreshMinInterval: float = 3600
    RetryCount: int = 3
    RetryTimeout: float = 60
    RetryBackoffFactor: float = 1
    RetryJitter: float = 1
    RetryMaxWaitInterval: float = 120
    ConsoleRetryCount: int = 1
    ConsoleRetryTimeout: float = 60
    ConsoleRetryBackoffFactor: float = 0
    ConsoleRetryJitter: int = 1
    ConsoleRetryMaxWaitInterval: float = 120
    ConsoleRetryErrCodes: Set = {
        APIErrorCode.ServerHighLoad.value,
        APIErrorCode.QPSLimitReached.value,
        APIErrorCode.ConsoleInternalError.value,
    }
    QpsLimit: float = 0
    RpmLimit: float = 0
    TpmLimit: int = 0
    DotEnvConfigFile: str = ".env"

    EnablePrivate: bool = False
    AccessCode: str = ""
    TruncatedContinuePrompt = "继续"
    ImportStatusPollingInterval: float = 2
    ExportStatusPollingInterval: float = 2
    ReleaseStatusPollingInterval: float = 2
    ETLStatusPollingInterval: float = 2
    TrainStatusPollingInterval: float = 30
    TrainerStatusPollingBackoffFactor: float = 3
    TrainerStatusPollingRetryTimes: float = 3
    ModelPublishStatusPollingInterval: float = 30
    BatchRunStatusPollingInterval: float = 30
    DeployStatusPollingInterval: float = 30
    DefaultFinetuneTrainType: str = "ERNIE-Speed"

    # 目前可直接下载到本地的千帆数据集解压后的大小上限
    # 后期研究更换为用户机内存大小的上限
    # 目前限制 2GB，防止用户内存爆炸
    ExportFileSizeLimit: int = 1024 * 1024 * 1024 * 2
    GetEntityContentFailedRetryTimes: int = 3

    EvaluationOnlinePollingInterval: float = 30
    BosHostRegion: str = "bj"
    RetryErrCodes: Set = {
        APIErrorCode.ServiceUnavailable.value,
        APIErrorCode.ServerHighLoad.value,
        APIErrorCode.QPSLimitReached.value,
        APIErrorCode.RPMLimitReached.value,
        APIErrorCode.TPMLimitReached.value,
    }
    SSLVerificationEnabled: bool = True
    Proxy: str = ""
    FileEncoding: str = "utf-8"


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
    ConsoleAPIQueryAction: str = "Action"
    FineTuneV2BaseRouteAPI: str = "/v2/finetuning"
    FineTuneCreateJobAction: str = "CreateFineTuningJob"
    FineTuneCreateTaskAction: str = "CreateFineTuningTask"
    FineTuneJobListAction: str = "DescribeFineTuningJobs"
    FineTuneTaskListAction: str = "DescribeFineTuningTasks"
    FineTuneTaskDetailAction: str = "DescribeFineTuningTask"
    FineTuneStopTaskAction: str = "StopFineTuningTask"
    FineTuneSupportedModelsAction: str = "DescribeFineTuningSupportModels"
    ModelDetailAPI: str = "/wenxinworkshop/modelrepo/modelDetail"
    ModelVersionDetailAPI: str = "/wenxinworkshop/modelrepo/modelVersionDetail"
    ModelPublishAPI: str = "/wenxinworkshop/modelrepo/publishTrainModel"
    ModelEvalCreateAPI: str = "/wenxinworkshop/modelrepo/eval/create"
    ModelEvalInfoAPI: str = "/wenxinworkshop/modelrepo/eval/detail"
    ModelEvalResultAPI: str = "/wenxinworkshop/modelrepo/eval/report"
    ModelEvalStopAPI: str = "/wenxinworkshop/modelrepo/eval/cancel"
    ModelPresetListAPI: str = "/wenxinworkshop/modelrepo/model/preset/list"
    ModelBatchDeleteAPI: str = "/wenxinworkshop/modelrepo/model/batchDelete"
    ModelVersionBatchDeleteAPI: str = (
        "/wenxinworkshop/modelrepo/model/version/batchDelete"
    )
    ModelUserListAPI: str = "/wenxinworkshop/modelrepo/model/user/list"
    ModelEvalResultExportAPI: str = "/wenxinworkshop/modelrepo/eval/result/export"
    ModelEvalResultExportStatusAPI: str = (
        "/wenxinworkshop/modelrepo/eval/result/export/info"
    )
    ModelEvaluableModelListAPI: str = "/wenxinworkshop/modelrepo/eval/model/list"
    ServiceCreateAPI: str = "/wenxinworkshop/service/apply"
    ServiceDetailAPI: str = "/wenxinworkshop/service/detail"
    ServiceListAPI: str = "/wenxinworkshop/service/list"
    DatasetCreateAPI: str = "/wenxinworkshop/dataset/create"
    DatasetReleaseAPI: str = "/wenxinworkshop/dataset/release"
    DatasetImportAPI: str = "/wenxinworkshop/dataset/import"
    DatasetInfoAPI: str = "/wenxinworkshop/dataset/info"
    DatasetStatusFetchInBatchAPI: str = "/wenxinworkshop/dataset/statusList"
    DatasetExportAPI: str = "/wenxinworkshop/dataset/export"
    DatasetDeleteAPI: str = "/wenxinworkshop/dataset/delete"
    DatasetExportRecordAPI: str = "/wenxinworkshop/dataset/exportRecord"
    DatasetImportErrorDetail: str = "/wenxinworkshop/dataset/importErrorDetail"
    DatasetCreateETLTaskAPI: str = "/wenxinworkshop/etl/create"
    DatasetETLTaskInfoAPI: str = "/wenxinworkshop/etl/detail"
    DatasetETLListTaskAPI: str = "/wenxinworkshop/etl/list"
    DatasetETLTaskDeleteAPI: str = "/wenxinworkshop/etl/delete"
    DatasetCreateAugTaskAPI: str = "/wenxinworkshop/enhance/create"
    DatasetAugListTaskAPI: str = "/wenxinworkshop/enhance/list"
    DatasetAugTaskInfoAPI: str = "/wenxinworkshop/enhance/detail"
    DatasetAugTaskDeleteAPI: str = "/wenxinworkshop/enhance/delete"
    DatasetAnnotateAPI: str = "/wenxinworkshop/entity/annotate"
    DatasetEntityDeleteAPI: str = "/wenxinworkshop/entity/delete"
    DatasetEntityListAPI: str = "/wenxinworkshop/entity/list"
    DatasetV2OfflineBatchInferenceAPI: str = "/v2/batchinference"
    DatasetCreateOfflineBatchInferenceAction: str = "CreateBatchInferenceTask"
    DatasetDescribeOfflineBatchInferenceAction: str = "DescribeBatchInferenceTask"
    PromptRenderAPI: str = "/rest/2.0/wenxinworkshop/api/v1/template/info"
    PromptCreateAPI: str = "/wenxinworkshop/prompt/template/create"
    PromptInfoAPI: str = "/wenxinworkshop/prompt/template/info"
    PromptUpdateAPI: str = "/wenxinworkshop/prompt/template/update"
    PromptDeleteAPI: str = "/wenxinworkshop/prompt/template/delete"
    PromptListAPI: str = "/wenxinworkshop/prompt/template/list"
    PromptLabelListAPI: str = "/wenxinworkshop/prompt/label/list"
    PromptCreateOptimizeTaskAPI: str = "/wenxinworkshop/prompt/singleOptimize/create"
    PromptGetOptimizeTaskInfoAPI: str = "/wenxinworkshop/prompt/singleOptimize/info"
    PromptEvaluationAPI: str = "/wenxinworkshop/prompt/evaluate/predict"
    PromptEvaluationSummaryAPI: str = "/wenxinworkshop/prompt/evaluate/summary"
    AppListAPI: str = "/wenxinworkshop/service/appList"
    EBTokenizerAPI: str = "/rpc/2.0/ai_custom/v1/wenxinworkshop/tokenizer/erniebot"

    ChargeAPI: str = "/v2/charge"
    ChargePurchaseQueryParam: str = "PurchaseTPMResource"
    ChargeInfoQueryParam: str = "DescribeTPMResource"
    ChargeStopQueryParam: str = "ReleaseTPMResource"

    STREAM_RESPONSE_PREFIX: str = "data: "
    STREAM_RESPONSE_EVENT_PREFIX: str = "event: "
    XRequestID: str = "Request_id"
    XResponseID: str = "X-Baidu-Request-Id"
    QianfanRequestIdDefaultPrefix: str = f"sdk-py-{VERSION}"


class DefaultLLMModel:
    """
    Defualt LLM model in qianfan sdk
    """

    Completion = "ERNIE-Bot-turbo"
    ChatCompletion = "ERNIE-Bot-turbo"
    Embedding = "Embedding-V1"
    Text2Image = "Stable-Diffusion-XL"


class PromptSceneType(int, enum.Enum):
    Text2Text: int = 1
    """文生文"""
    Text2Image: int = 2
    """文生图"""


class PromptFrameworkType(int, enum.Enum):
    NotUse: int = 0
    """不使用框架"""
    Basic: int = 1
    """基础框架"""
    CRISPE: int = 2
    """CRISPE框架"""
    Fewshot: int = 3
    """fewshot框架"""


class PromptType(int, enum.Enum):
    Preset = 1
    """预置模版"""
    User = 2
    """用户创建模版"""


class PromptScoreStandard(int, enum.Enum):
    Semantic = 1
    """语义相似"""
    Regex = 2
    """正则匹配"""
    Exact = 3
    """精准匹配"""
