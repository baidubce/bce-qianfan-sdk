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
import threading

import pytest

import qianfan
from qianfan.tests.utils import EnvHelper, init_test_env
from qianfan.tests.utils.consts import Consts
from qianfan.utils.logging import log_debug


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
        QIANFAN_ACCESS_KEY=Consts.test_access_key,
        QIANFAN_SECRET_KEY=Consts.test_secret_key,
        QIANFAN_TRAIN_STATUS_POLLING_INTERVAL="1",
        QIANFAN_DEPLOY_STATUS_POLLING_INTERVAL="1",
        QIANFAN_MODEL_PUBLISH_STATUS_POLLING_INTERVAL="1",
    ):
        yield


@pytest.fixture(autouse=True, scope="function")
def reset_config_automatically():
    qianfan.config._GLOBAL_CONFIG = None
    return


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_setup(item):
    # 记录测试开始时的活动线程数
    item._initial_thread_count = threading.active_count()
    item._initial_threads = {
        thread.ident: thread.name for thread in threading.enumerate()
    }
    yield


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_teardown(item):
    yield
    # 记录测试结束时的活动线程数
    final_thread_count = threading.active_count()
    initial_thread_count = getattr(item, "_initial_thread_count", final_thread_count)

    # 计算新增的线程数
    threads_created = final_thread_count - initial_thread_count
    log_debug(
        f" '{item.nodeid}' thread stat: init:{initial_thread_count}, curr: "
        f" {final_thread_count} , new threads count: {threads_created}"
    )

    # 列出diff threads
    final_threads = {thread.ident: thread.name for thread in threading.enumerate()}
    initial_threads = getattr(item, "_initial_threads", final_threads)
    # 找出新增的线程
    new_threads = {
        ident: name
        for ident, name in final_threads.items()
        if ident not in initial_threads
    }
    # 打印新增的线程信息
    log_debug(f"ut: '{item.nodeid}' new threads count: {len(new_threads)}")
    for ident, name in new_threads.items():
        log_debug(
            f"thread ID: {ident}, thread name: {name}",
        )
