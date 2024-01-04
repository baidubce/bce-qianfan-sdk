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

import qianfan
from qianfan.resources.auth.oauth import Auth
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


@pytest.fixture(autouse=True, scope="function")
def reset_config_automatically():
    qianfan.config._GLOBAL_CONFIG = None
    return


def reset_config():
    qianfan.config._GLOBAL_CONFIG = None
    return


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
        reset_config()
        access_token = "access_token_from_env_8896281"
        with EnvHelper(QIANFAN_ACCESS_TOKEN=access_token):
            # if user provides access_token again for same (ak, sk)
            auth = Auth()
            ak = os.environ["QIANFAN_AK"]
            sk = os.environ["QIANFAN_SK"]
            # should use the newly provided access_token
            assert auth.access_token() == access_token
            auth.refresh_access_token()
            # after refresh, should use new access_token
            assert auth.access_token() == fake_access_token(ak, sk)


def test_access_token_from_args():
    """
    test access_token with args
    """
    with EnvHelper(QIANFAN_AK="ak_from_env_584183", QIANFAN_SK="sk_from_env_531457"):
        env_access_token = "access_token_from_env_should_not_be_used"
        with EnvHelper(QIANFAN_ACCESS_TOKEN=env_access_token):
            access_token = "access_token_from_args_156848"
            auth = Auth(access_token=access_token)
            ak = os.environ["QIANFAN_AK"]
            sk = os.environ["QIANFAN_SK"]
            # should use provided access_token from args
            assert auth.access_token() == access_token
            # after refresh, should use new access_token
            auth.refresh_access_token()
            assert auth.access_token() == fake_access_token(ak, sk)
            access_token = "access_token_from_args_284915"
            # if user provides access_token again for same (ak, sk)
            auth = Auth(access_token=access_token)
            ak = os.environ["QIANFAN_AK"]
            sk = os.environ["QIANFAN_SK"]
            # should use the newly provided access_token
            assert auth.access_token() == access_token
            auth.refresh_access_token()
            # after refresh, should use new access_token
            assert auth.access_token() == fake_access_token(ak, sk)
            ak = "ak_from_args_358796"
            sk = "sk_from_args_513578"
            auth = Auth(ak=ak, sk=sk, access_token=access_token)
            # should use provided access_token from args
            assert auth.access_token() == access_token
            auth.refresh_access_token()
            assert auth.access_token() == fake_access_token(ak, sk)
        reset_config()
        # test global function
        ak = "ak_from_function_1"
        sk = "sk_from_function_1"
        qianfan.AK(ak)
        qianfan.SK(sk)
        auth = Auth()
        assert auth.access_token() == fake_access_token(ak, sk)
        access_token = "access_token_from_function_1"
        qianfan.AccessToken(access_token)
        auth = Auth()
        assert auth.access_token() == access_token
        auth.refresh_access_token()
        assert auth.access_token() == fake_access_token(ak, sk)
        ak = "ak_from_args_348126"
        sk = "sk_from_args_956158"
        auth = Auth(ak=ak, sk=sk)
        # should use provided access_token from args
        assert auth.access_token() == access_token
        auth.refresh_access_token()
        assert auth.access_token() == fake_access_token(ak, sk)
        qianfan.AccessToken(None)
        ak = "ak_from_args_998416"
        sk = "sk_from_args_841523"
        auth = Auth(ak=ak, sk=sk)
        # should use provided access_token from args
        assert auth.access_token() == fake_access_token(ak, sk)
        qianfan.AK(None)
        qianfan.SK(None)


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
        reset_config()
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


@pytest.mark.asyncio
async def test_access_token_from_args_async():
    """
    test access_token with args
    """
    with EnvHelper(QIANFAN_AK="ak_from_env_357223", QIANFAN_SK="sk_from_env_782215"):
        env_access_token = "access_token_from_env_should_not_be_used"
        with EnvHelper(QIANFAN_ACCESS_TOKEN=env_access_token):
            access_token = "access_token_from_args_987521"
            auth = Auth(access_token=access_token)
            ak = os.environ["QIANFAN_AK"]
            sk = os.environ["QIANFAN_SK"]
            # should use provided access_token from args
            assert await auth.a_access_token() == access_token
            # after refresh, should use new access_token
            await auth.arefresh_access_token()
            assert await auth.a_access_token() == fake_access_token(ak, sk)
            access_token = "access_token_from_args_789621"
            # if user provides access_token again for same (ak, sk)
            auth = Auth(access_token=access_token)
            ak = os.environ["QIANFAN_AK"]
            sk = os.environ["QIANFAN_SK"]
            # should use the newly provided access_token
            assert await auth.a_access_token() == access_token
            await auth.arefresh_access_token()
            # after refresh, should use new access_token
            assert await auth.a_access_token() == fake_access_token(ak, sk)
            ak = "ak_from_args_358796"
            sk = "sk_from_args_513578"
            auth = Auth(ak=ak, sk=sk, access_token=access_token)
            # should use provided access_token from args
            assert await auth.a_access_token() == access_token
            await auth.arefresh_access_token()
            assert await auth.a_access_token() == fake_access_token(ak, sk)
        reset_config()
        # test global function
        ak = "ak_from_function_1"
        sk = "sk_from_function_1"
        qianfan.AK(ak)
        qianfan.SK(sk)
        auth = Auth()
        assert await auth.a_access_token() == fake_access_token(ak, sk)
        access_token = "access_token_from_function_1"
        qianfan.AccessToken(access_token)
        auth = Auth()
        assert await auth.a_access_token() == access_token
        await auth.arefresh_access_token()
        assert await auth.a_access_token() == fake_access_token(ak, sk)
        ak = "ak_from_args_348126"
        sk = "sk_from_args_956158"
        auth = Auth(ak=ak, sk=sk)
        # should use provided access_token from args
        assert await auth.a_access_token() == access_token
        await auth.arefresh_access_token()
        assert await auth.a_access_token() == fake_access_token(ak, sk)
        qianfan.AccessToken(None)
        ak = "ak_from_args_998416"
        sk = "sk_from_args_841523"
        auth = Auth(ak=ak, sk=sk)
        # should use provided access_token from args
        assert await auth.a_access_token() == fake_access_token(ak, sk)
        qianfan.AK(None)
        qianfan.SK(None)


def test_auth_from_access_key():
    with EnvHelper(QIANFAN_ACCESS_KEY="access_key", QIANFAN_SECRET_KEY="secret_key"):
        qianfan.get_config().AK = None
        qianfan.get_config().SK = None
        auth = Auth()
        assert auth.access_token() == ""

        qianfan.get_config().AK = "ak_111"
        auth = Auth()
        assert auth.access_token() == ""

        qianfan.get_config().ACCESS_TOKEN = "access_token_111"
        auth = Auth()
        assert auth.access_token() == "access_token_111"


@pytest.mark.asyncio
async def test_auth_from_access_key_async():
    with EnvHelper(QIANFAN_ACCESS_KEY="access_key", QIANFAN_SECRET_KEY="secret_key"):
        qianfan.get_config().AK = None
        qianfan.get_config().SK = None
        auth = Auth()
        assert await auth.a_access_token() == ""

        qianfan.get_config().AK = "ak_111"
        auth = Auth()
        assert await auth.a_access_token() == ""

        qianfan.get_config().ACCESS_TOKEN = "access_token_111"
        auth = Auth()
        assert await auth.a_access_token() == "access_token_111"
