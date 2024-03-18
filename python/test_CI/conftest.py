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
    Unit test config for cookbook
"""
import os
import pytest
from utils.cookbook_operate import CookbookExecutor


def pytest_addoption(parser):
    """
    为 pytest 插件添加选项

    Args:
        parser (argparse.ArgumentParser): 命令行参数解析器

    Returns:
        None

    """
    parser.addoption("--ak", default="")
    parser.addoption("--sk", default="")
    parser.addoption("--root-dir", default="")
    parser.addoption("--keywords", default="{}")


@pytest.fixture(scope='session', autouse=True)
def env_set(request):
    """
    根据命令行参数设置环境变量，测试结束时会删除环境变量。

    Args:
        request (object): Flask请求对象，其中包含了命令行参数信息。

    Returns:

    """
    if request.config.getoption('--ak') != '':
        os.environ['QIANFAN_ACCESS_KEY'] = request.config.getoption("--ak").replace('"', '').replace("'", '')
    if request.config.getoption('--sk') != '':
        os.environ['QIANFAN_SECRET_KEY'] = request.config.getoption("--sk").replace('"', '').replace("'", '')
    if request.config.getoption('--keywords') != '{}':
        os.environ['KEYWORDS_DICT'] = request.config.getoption("--keywords")
    if request.config.getoption('--root-dir') != '':
        os.environ['ROOT_DIR'] = request.config.getoption("--root-dir")
    else:
        os.environ['ROOT_DIR'] = '../..'

    other_env = [('RetryCount', '3'), ('QIANFAN_QPS_LIMIT', '1'), ('QIANFAN_LLM_API_RETRY_COUNT', '3')]
    for key, value in other_env:
        os.environ[key] = value

    yield
    if os.environ.get('QIANFAN_ACCESS_KEY'):
        del os.environ['QIANFAN_ACCESS_KEY']
    if os.environ.get('QIANFAN_SECRET_KEY'):
        del os.environ['QIANFAN_SECRET_KEY']
    if os.environ.get('KEYWORDS_DICT'):
        del os.environ['KEYWORDS_DICT']
    if os.environ.get('ROOT_DIR'):
        del os.environ['ROOT_DIR']
    for key, value in other_env:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="function")
def executor():
    """
    创建一个CookbookExecutor对象并返回，开始测试。

    Args:
        无参数。

    Returns:
        CookbookExecutor对象。

    """
    with CookbookExecutor() as e:
        yield e
