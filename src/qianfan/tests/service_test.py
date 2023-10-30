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
    Unit test for FineTune
"""


from qianfan import Service


def test_create_service():
    """
    test Service.create
    """
    resp = Service.create(
        model_id=846,
        model_version_id=168,
        name="sdk_test",
        uri="sdk_ut",
        replicas=1,
        pool_type=2,
        description="description_ut",
    )
    assert resp["_request"] == {
        "modelId": 846,
        "modelVersionId": 168,
        "name": "sdk_test",
        "uri": "sdk_ut",
        "replicas": 1,
        "poolType": 2,
        "description": "description_ut",
    }
    result = resp["result"]
    assert "result" in result
    assert "serviceId" in result


def test_service_detail():
    """
    test Service.detail
    """
    resp = Service.get(id=108)
    assert resp["_request"] == {"serviceId": 108}
    assert "vmConfig" in resp["result"]
    assert "creator" in resp["result"]
