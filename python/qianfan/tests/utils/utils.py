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

import logging
import os
import time

import requests

import qianfan
from qianfan.consts import Env
from qianfan.tests.utils.mock_server import start_mock_server


def init_test_env():
    """
    init for test environment
    """
    os.environ[Env.BaseURL] = "http://127.0.0.1:8866"
    os.environ[Env.ConsoleAPIBaseURL] = "http://127.0.0.1:8866"
    os.environ[Env.DisableErnieBotSDK] = "True"
    os.environ[Env.IAMBaseURL] = "http://127.0.0.1:8866"
    qianfan.enable_log(logging.INFO)
    if "QIANFAN_AK" in os.environ:
        os.environ.pop("QIANFAN_AK")
    if "QIANFAN_SK" in os.environ:
        os.environ.pop("QIANFAN_SK")
    start_mock_server()
    # ensure the mock server is ready
    for _ in range(50):
        try:
            requests.get("http://127.0.0.1:8866/")
            break
        except Exception:
            time.sleep(0.2)


class EnvHelper(object):
    """
    this is a helper class for setting environment
    """

    def __init__(self, **kwargs):
        """
        init helper, accept ak and sk
        """
        self._env_list = kwargs
        self._old_env = {}

    def _set_environ(self, env_name, value):
        """
        set environment variable and if value is None, unset it
        """
        if value is None:
            os.environ.pop(env_name)
        else:
            os.environ[env_name] = value
        qianfan.config._GLOBAL_CONFIG = None

    def __enter__(self):
        """
        set environment when entering
        """
        for env_name, value in self._env_list.items():
            self._old_env[env_name] = os.environ.get(env_name, None)
            self._set_environ(env_name, value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        unset environment when leaving
        """
        for env_name, old_value in self._old_env.items():
            self._set_environ(env_name, old_value)
