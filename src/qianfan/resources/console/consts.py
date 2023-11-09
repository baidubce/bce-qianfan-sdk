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
    GenericText: int = 401
    QuerySet: int = 402
    Text2Speech: int = 705


class DataTemplateType(int, Enum):
    """
    Template type used by Qianfan Data
    """

    NonAnnotatedConversation: int = 2000
    AnnotatedConversation: int = 2001
    GenericText: int = 40100
    QuerySet: int = 40200
    Text2Speech: int = 70500


class DataSetType(int, Enum):
    TextOnly: int = 4
    MultiModel: int = 7


class DataStorageType(str, Enum):
    PublicBos: str = "sysBos"
    PrivateBos: str = "usrBos"


class DataSourceType(int, Enum):
    PrivateBos: int = 1
    SharedZipUrl: int = 2


class DataExportDestinationType(int, Enum):
    PlatformBos: int = 0
    PrivateBos: int = 1


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
    NotStarted: int = -1
    """未发起发布"""
    Initialized: int = 0
    """发布初始化"""
    Running: int = 1
    """发布进行中"""
    Finished: int = 2
    """发布完成"""
    Failed: int = 3
    """发布失败"""
