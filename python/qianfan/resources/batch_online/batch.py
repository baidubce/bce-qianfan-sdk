# Copyright (c) 2025 Baidu, Inc. All Rights Reserved.
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

from .chat import AsyncChat, Chat
from .images import AsyncImages, Images
from ...config import get_config

__all__ = ["Batch", "AsyncBatch"]

class Batch:

    def chat(self) -> Chat:
        return Chat()

    def images(self) -> Images:
        return Images()


class AsyncBatch:

    def chat(self) -> AsyncChat:
        return AsyncChat()

    def images(self) -> AsyncImages:
        return AsyncImages()


