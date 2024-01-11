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
"""summary of utils
"""

from qianfan.utils.logging import (
    disable_log,
    enable_log,
    log_debug,
    log_error,
    log_info,
    log_warn,
    logger,
)
from qianfan.utils.utils import (
    AsyncLock,
    _get_from_env_or_default,
    _get_value_from_dict_or_var_or_env,
    _none_if_empty,
    _set_val_if_key_exists,
    _strtobool,
)

__all__ = [
    "logger",
    "log_info",
    "log_debug",
    "log_error",
    "log_warn",
    "enable_log",
    "disable_log",
    "_get_from_env_or_default",
    "_get_value_from_dict_or_var_or_env",
    "_none_if_empty",
    "_set_val_if_key_exists",
    "_strtobool",
    "AsyncLock",
]
