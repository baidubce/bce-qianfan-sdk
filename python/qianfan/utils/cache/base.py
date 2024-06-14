# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
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
from typing import Any

from diskcache import Cache

from qianfan.config import get_config
from qianfan.utils.helper import Singleton
from qianfan.utils.logging import log_info


class KvCache(Cache, metaclass=Singleton):
    def __init__(self, **kwargs: Any) -> None:
        if get_config().DISABLE_CACHE:
            log_info("cache is disabled, reset `QIANFAN_DISABLE_CACHE` if needed")
            return
        super().__init__(directory=get_config().CACHE_DIR, **kwargs)

    def get(self, **kwargs: Any) -> Any:
        if get_config().DISABLE_CACHE:
            return None
        return super().get(**kwargs)

    def set(self, **kwargs: Any) -> Any:
        if get_config().DISABLE_CACHE:
            return None
        return super().set(**kwargs)
