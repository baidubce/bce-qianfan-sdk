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
Library aimed to helping developer to interactive with LLM.
"""

from qianfan.config import AK, SK, AccessKey, AccessToken, SecretKey, get_config
from qianfan.resources import (
    ChatCompletion,
    Completion,
    Embedding,
    Image2Text,
    Plugin,
    QfMessages,
    QfResponse,
    QfRole,
    Text2Image,
    Tokenizer,
)
from qianfan.utils import disable_log, enable_log
from qianfan.version import VERSION

Role = QfRole
Messages = QfMessages
Response = QfResponse

__all__ = [
    "ChatCompletion",
    "Embedding",
    "Completion",
    "Plugin",
    "Text2Image",
    "Image2Text",
    "Tokenizer",
    "AK",
    "SK",
    "Role",
    "Messages",
    "Response",
    "QfRole",
    "QfMessages",
    "QfResponse",
    "AccessToken",
    "AccessKey",
    "SecretKey",
    "get_config",
    "disable_log",
    "enable_log",
]
__version__ = VERSION
