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
    Unit test for ChatCompletion
"""

import os

import pytest

from qianfan.resources.auth import Auth
from qianfan.tests.utils import EnvHelper, init_test_env
from qianfan.tests.utils.mock_server import fake_access_token


@pytest.fixture(autouse=True, scope="module")
def init():
    """
    Init test
    start the mock server first
    """
    init_test_env()
    yield


def set_env_ak_sk(ak=None, sk=None):
    """
    set env variables value for ak and sk
    """
    if ak is not None:
        os.environ["QIANFAN_AK"] = ak
    if sk is not None:
        os.environ["QIANFAN_SK"] = sk


def test_auth_from_env():
    """
    test auth with environment variables
    """
    with EnvHelper(QIANFAN_AK="ak_from_env_438957", QIANFAN_SK="sk_from_env_438987)"):
        ak = os.environ["QIANFAN_AK"]
        sk = os.environ["QIANFAN_SK"]
        auth = Auth()
        assert auth.access_token() == fake_access_token(ak, sk)


def test_auth_from_args():
    """
    test auth with args
    """
    with EnvHelper(
        QIANFAN_AK="ak_should_not_be_used", QIANFAN_SK="sk_should_not_be_used"
    ):
        ak = "ak_from_ut_186548156"
        sk = "sk_from_ut_511856265"
        auth = Auth(ak=ak, sk=sk)
        assert auth.access_token() == fake_access_token(ak, sk)
        ak = "ak_from_ut_2994j9fd6"
        sk = "sk_from_ut_656545265"
        auth = Auth(ak=ak, sk=sk)
        assert auth.access_token() == fake_access_token(ak, sk)


def test_access_token_from_env():
    """
    test access_token with environment variables
    """
    with EnvHelper(QIANFAN_AK="ak_from_env_464587", QIANFAN_SK="sk_from_env_498647"):
        access_token = "access_token_from_env_1868481"
        with EnvHelper(QIANFAN_ACCESS_TOKEN=access_token):
            auth = Auth()
            ak = os.environ["QIANFAN_AK"]
            sk = os.environ["QIANFAN_SK"]
            # should use provided access_token
            assert auth.access_token() == access_token
            # after refresh, should use new access_token
            auth.refresh_access_token()
            assert auth.access_token() == fake_access_token(ak, sk)
        access_token = "access_token_from_env_8896281"
        with EnvHelper(QIANFAN_ACCESS_TOKEN=access_token):
            os.environ["QIANFAN_ACCESS_TOKEN"] = access_token
            # if user provides access_token again for same (ak, sk)
            auth = Auth()
            ak = os.environ["QIANFAN_AK"]
            sk = os.environ["QIANFAN_SK"]
            # should use the newly provided access_token
            assert auth.access_token() == access_token
            auth.refresh_access_token()
            # after refresh, should use new access_token
            assert auth.access_token() == fake_access_token(ak, sk)


@pytest.mark.asyncio
async def test_auth_from_args_async():
    """
    test auth with args
    """
    with EnvHelper(
        QIANFAN_AK="ak_should_not_be_used", QIANFAN_SK="sk_should_not_be_used"
    ):
        ak = "ak_from_ut_186548156"
        sk = "sk_from_ut_511856265"
        auth = Auth(ak=ak, sk=sk)
        assert await auth.a_access_token() == fake_access_token(ak, sk)
        ak = "ak_from_ut_2994j9fd6"
        sk = "sk_from_ut_656545265"
        auth = Auth(ak=ak, sk=sk)
        assert await auth.a_access_token() == fake_access_token(ak, sk)


@pytest.mark.asyncio
async def test_access_token_from_env_async():
    """
    test access_token with environment variables
    """
    with EnvHelper(QIANFAN_AK="ak_from_env_464587", QIANFAN_SK="sk_from_env_498647"):
        access_token = "access_token_from_env_1868481"
        with EnvHelper(QIANFAN_ACCESS_TOKEN=access_token):
            auth = Auth()
            ak = os.environ["QIANFAN_AK"]
            sk = os.environ["QIANFAN_SK"]
            # should use provided access_token
            assert await auth.a_access_token() == access_token
            # after refresh, should use new access_token
            await auth.arefresh_access_token()
            assert await auth.a_access_token() == fake_access_token(ak, sk)
        access_token = "access_token_from_env_8896281"
        with EnvHelper(QIANFAN_ACCESS_TOKEN=access_token):
            os.environ["QIANFAN_ACCESS_TOKEN"] = access_token
            # if user provides access_token again for same (ak, sk)
            auth = Auth()
            ak = os.environ["QIANFAN_AK"]
            sk = os.environ["QIANFAN_SK"]
            # should use the newly provided access_token
            assert await auth.a_access_token() == access_token
            await auth.arefresh_access_token()
            # after refresh, should use new access_token
            assert await auth.a_access_token() == fake_access_token(ak, sk)
