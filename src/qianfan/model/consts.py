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
from enum import Enum
from typing import Any, Dict

from qianfan.resources import ChatCompletion, Completion, Embedding, Text2Image


class ServiceType(str, Enum):
    Chat = "Chat"
    """Corresponding to the `ChatCompletion`"""
    Completion = "Completion"
    """Corresponding to the `Completion`"""
    Embedding = "Embedding"
    """Corresponding to the `Embedding`"""
    Text2Image = "Text2Image"
    """Corresponding to the `Text2Image"""


# service type -> resources class
ServiceTypeResourcesMapping: Dict[ServiceType, Any] = {
    ServiceType.Chat: ChatCompletion,
    ServiceType.Completion: Completion,
    ServiceType.Embedding: Embedding,
    ServiceType.Text2Image: Text2Image,
}
