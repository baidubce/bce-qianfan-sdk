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
    Unit test for Reranker 
"""
import pytest

import qianfan
import qianfan.tests.utils

_QUERY = "北京的天气"
_DOCUMENTS = ["北京今天12.5度，北风，阴天", "北京美食很多"]


def test_reranker_do():
    """
    Test basic reranker
    """
    # qfg = qianfan.Reranker(endpoint="fuyu1")
    r = qianfan.Reranker()
    resp = r.do(_QUERY, _DOCUMENTS)
    assert isinstance(resp["body"]["results"], list)

    r = qianfan.Reranker(model="bce-reranker-base_v1")
    resp = r.do(_QUERY, _DOCUMENTS)

    resp = r.do(_QUERY, _DOCUMENTS, top_n=1)
    assert len(resp["body"]["results"]) == 1


@pytest.mark.asyncio
async def test_reranker_ado():
    """
    Test basic async reranker
    """
    r = qianfan.Reranker()
    resp = r.do(_QUERY, _DOCUMENTS)
    assert isinstance(resp["body"]["results"], list)

    r = qianfan.Reranker(model="bce-reranker-base_v1")
    resp = r.do(_QUERY, _DOCUMENTS)

    resp = r.do(_QUERY, _DOCUMENTS, top_n=1)
    assert len(resp["body"]["results"]) == 1
