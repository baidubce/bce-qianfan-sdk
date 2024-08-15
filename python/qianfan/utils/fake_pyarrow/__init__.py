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
fake pyarrow package
"""

from qianfan.utils.fake_pyarrow.functions import concat_tables
from qianfan.utils.fake_pyarrow.table import ChunkedArray, Table
from qianfan.utils.logging import log_warn

is_fake = True

log_warn(
    "no pyarrow has been installed. Dataset will run in restrict mode in which some"
    " functions may not be available"
)

__all__ = [
    "Table",
    "concat_tables",
    "ChunkedArray",
    "is_fake",
]
