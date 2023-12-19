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
User constants when using resources
"""

from enum import Enum


class DataProjectType(int, Enum):
    """
    Project type used by Qianfan Data
    """

    Conversation: int = 20
    """对话类"""
    GenericText: int = 401
    """返文本类"""
    QuerySet: int = 402
    """Query 查询类"""
    Text2Image: int = 705
    """文生图类"""


class DataTemplateType(int, Enum):
    """
    Template type used by Qianfan Data
    """

    NonSortedConversation: int = 2000
    """非排序对话"""
    SortedConversation: int = 2001
    """含排序对话"""
    GenericText: int = 40100
    """泛文本"""
    QuerySet: int = 40200
    """Query 查询"""
    Text2Image: int = 70500
    """文生图"""


class DataSetType(int, Enum):
    TextOnly: int = 4
    """文本类数据集"""
    MultiModel: int = 7
    """多模态数据集"""


class DataStorageType(str, Enum):
    PublicBos: str = "sysBos"
    """平台公共 Bos"""
    PrivateBos: str = "usrBos"
    """用户私有 Bos"""


class DataSourceType(int, Enum):
    PrivateBos: int = 1
    """私有 Bos"""
    SharedZipUrl: int = 2
    """包含 zip 压缩包的分享链接"""


class DataExportDestinationType(int, Enum):
    PlatformBos: int = 0
    """导出到平台 Bos"""
    PrivateBos: int = 1
    """导出到私有 Bos"""


class DataImportStatus(int, Enum):
    NotStarted: int = -1
    """未发起导入"""
    Initialized: int = 0
    """导入初始化"""
    Running: int = 1
    """导入进行中"""
    Finished: int = 2
    """导入完成"""
    Failed: int = 3
    """导入失败"""
    Terminated: int = 4
    """导入终止"""


class DataExportStatus(int, Enum):
    NotStarted: int = -1
    """未发起导出"""
    Initialized: int = 0
    """导出初始化"""
    Running: int = 1
    """导出进行中"""
    Finished: int = 2
    """导出完成"""
    Failed: int = 3
    """导出失败"""


class DataReleaseStatus(int, Enum):
    NotStarted: int = 0
    """未发起发布"""
    Running: int = 1
    """发布进行中"""
    Finished: int = 2
    """发布完成"""
    Failed: int = 3
    """发布失败"""


class ServiceStatus(str, Enum):
    Done = "Done"
    """服务就绪"""
    New = "New"
    """服务新建"""
    Deploying = "Deploying"
    """服务部署中"""
    Failed = "Failed"
    """服务部署失败"""
    Stopped = "Stopped"
    """服务下线"""


class TrainStatus(str, Enum):
    Finish = "FINISH"
    """训练完成"""
    Running = "RUNNING"
    """训练进行中"""
    Fail = "FAIL"
    """训练失败"""
    Stop = "STOP"
    """训练停止"""


class ModelState(str, Enum):
    Ready = "Ready"
    """已就绪"""
    Creating = "Creating"
    """创建中"""
    Fail = "Fail"
    """创建失败"""


class TrainDatasetType(int, Enum):
    Platform = 1
    """平台数据集"""
    PrivateBos = 2
    """私有Bos数据集"""


class TrainMode(str, Enum):
    SFT = "SFT"
    """对应 LLMFinetune"""


class DeployPoolType(int, Enum):
    PublicResource = 1
    PrivateResource = 2


class EntityListingType(int, Enum):
    All: int = 0
    """展示全部"""
    AnnotatedOnly: int = 1
    """只展示已标注的"""
    NotAnnotatedOnly: int = 2
    """只展示未标注的"""


class ETLTaskStatus(int, Enum):
    NoTask: int = 0
    """没有任务"""
    Running: int = 1
    """清洗中"""
    Finished: int = 2
    """清洗完成"""
    Interrupted: int = 3
    """清洗被终止"""
    Failed: int = 4
    """清洗失败"""
    Paused: int = 5
    """清洗暂停"""


class EvaluationTaskStatus(str, Enum):
    Pending: str = "Pending"
    """任务已提交，待调度"""
    Doing: str = "Doing"
    """任务已调度，执行中"""
    DoingWithManualBegin: str = "DoingWithManualBegin"
    """运行中（可人工标注）"""
    Stopping: str = "Stopping"
    """任务停止中"""
    Done: str = "Done"
    """评估任务全部评估成功"""
    PartlyDone: str = "PartlyDone"
    """评估任务部分评估成功"""
    Failed: str = "Failed"
    """评估任务全部失败"""
    Stopped: str = "Stopped"
    """任务已全部停止"""
