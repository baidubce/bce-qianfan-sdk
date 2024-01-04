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
    Unit test for retry
"""

import pytest

import qianfan
from qianfan.errors import APIError
from qianfan.tests.utils import EnvHelper


def test_retry_accesstoken_expired():
    """
    Test retry access token expired
    """
    access_token = "expired"
    with EnvHelper(QIANFAN_ACCESS_TOKEN=access_token):
        comp = qianfan.Completion()
        assert comp.access_token() == access_token
        resp = comp.do(prompt="test")
        assert resp is not None
        assert resp["code"] == 200
        assert "id" in resp["body"]
        assert resp["object"] == "completion"
        assert comp.access_token() != access_token


def test_retry_retry_cnt():
    """
    Test retry
    """
    comp = qianfan.Completion(endpoint="test_retry")
    with pytest.raises(APIError):
        resp = comp.do(prompt="test", retry_count=10, retry_err_codes=[1])

    comp = qianfan.Completion(endpoint="test_retry1")
    with pytest.raises(APIError):
        resp = comp.do(prompt="test", retry_count=1)
        assert resp is not None
        assert resp["code"] == 200
        assert "id" in resp["body"]
        assert resp["object"] == "completion"    

    comp = qianfan.Completion(endpoint="test_retry2")
    resp = comp.do(prompt="test", retry_count=3)
    assert resp is not None
    assert resp["code"] == 200
    assert "id" in resp["body"]
    assert resp["object"] == "completion"


@pytest.mark.asyncio
async def test_async_retry_retry_cnt():
    """
    Test async retry
    """
    comp = qianfan.Completion(endpoint="test_retry")

    with pytest.raises(APIError):
        resp = await comp.ado(prompt="test", retry_count=1)
        assert resp is not None
        assert resp["code"] == 200
        assert "id" in resp["body"]
        assert resp["object"] == "completion"

    resp = await comp.ado(prompt="test", retry_count=4)
    assert resp is not None
    assert resp["code"] == 200
    assert "id" in resp["body"]
    assert resp["object"] == "completion"
