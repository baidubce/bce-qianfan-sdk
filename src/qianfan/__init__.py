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
Library that wraps the qianfan API.
"""


from qianfan.config import AK, SK, AccessKey, AccessToken, SecretKey, get_config
from qianfan.resources.console.finetune import FineTune
from qianfan.resources.console.model import Model
from qianfan.resources.console.service import Service
from qianfan.resources.images.text2image import Text2Image
from qianfan.resources.llm.chat_completion import ChatCompletion
from qianfan.resources.llm.completion import Completion
from qianfan.resources.llm.embedding import Embedding
from qianfan.resources.llm.plugin import Plugin
from qianfan.resources.tools.tokenizer import Tokenizer
from qianfan.resources.typing import QfMessages, QfResponse, QfRole
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
    "FineTune",
    "Model",
    "Service",
    "Text2Image",
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
