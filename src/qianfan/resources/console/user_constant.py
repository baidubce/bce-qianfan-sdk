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
    Local: int = 0
    PrivateBos: int = 1
    SharedZipUrl: int = 2


class DataZipInnerContentFormatType(int, Enum):
    Json: int = 2
    xml_voc: int = 3


class DataExportScene(int, Enum):
    Normal: int = 0
    Release: int = 1
