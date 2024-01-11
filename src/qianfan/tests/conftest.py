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
    test config for qianfan pytest
"""
import pytest

import qianfan
from qianfan.tests.utils import EnvHelper, init_test_env


@pytest.fixture(autouse=True, scope="session")
def init():
    """
    Init test
    start the mock server first and set the ak/sk
    """
    init_test_env()
    with EnvHelper(
        QIANFAN_AK="test_ak",
        QIANFAN_SK="test_sk",
        QIANFAN_ACCESS_KEY="test_access_key",
        QIANFAN_SECRET_KEY="test_secret_key",
        QIANFAN_TRAIN_STATUS_POLLING_INTERVAL="1",
        QIANFAN_DEPLOY_STATUS_POLLING_INTERVAL="1",
        QIANFAN_MODEL_PUBLISH_STATUS_POLLING_INTERVAL="1",
    ):
        yield


@pytest.fixture(autouse=True, scope="function")
def reset_config_automatically():
    qianfan.config._GLOBAL_CONFIG = None
    return
