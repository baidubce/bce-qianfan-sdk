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
    Unit test for config
"""
from qianfan import get_config
from qianfan.consts import DefaultValue


def test_rewrite_config_through_code():
    config_center = get_config()
    assert get_config().AUTH_TIMEOUT == DefaultValue.AuthTimeout
    config_center.AUTH_TIMEOUT = 114514
    assert get_config().AUTH_TIMEOUT == 114514
