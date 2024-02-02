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


from qianfan.resources import Service
from qianfan.resources.console.consts import DeployPoolType, ServiceType
from qianfan.version import VERSION


def test_create_service():
    """
    test Service.create
    """
    #  test all deploy config
    resp = Service.create(
        model_id=846,
        model_version_id=168,
        name="sdk_test",
        uri="sdk_ut",
        replicas=1,
        pool_type=DeployPoolType.PrivateResource,
        description="description_ut",
    )
    assert resp["_request"] == {
        "modelId": 846,
        "modelVersionId": 168,
        "name": "sdk_test",
        "uri": "sdk_ut",
        "replicas": 1,
        "poolType": DeployPoolType.PrivateResource,
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


def test_service_list():
    """
    test Service.list
    """
    resp = Service.list()
    assert resp["_request"] == {}
    assert "custom" in resp["result"]
    assert "common" in resp["result"]

    for item in list(ServiceType):
        resp = Service.list(api_type_filter=[item])
        for common_service in resp["result"]["common"]:
            assert common_service["apiType"] == item.value


def test_sdk_console_indicator():
    res = Service.list()
    # header不区分大小写，flask受到后将起转换成大写：
    assert res["_header"]["Request-Source"] == f"qianfan_py_sdk_v{VERSION}"
