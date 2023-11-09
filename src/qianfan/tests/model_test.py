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


from qianfan.resources import Model


def test_list_model():
    """
    test Model.list
    """
    resp = Model.list(model_id=643)
    assert resp["_request"] == {"modelId": 643}
    result = resp["result"]
    assert "modelId" in result
    assert "modelVersionList" in result


def test_model_detail():
    """
    test Model.detail
    """
    resp = Model.detail(model_version_id=851)
    assert resp["_request"] == {"modelVersionId": 851}
    assert "modelId" in resp["result"]
    assert "params" in resp["result"]


def test_publish_model():
    """
    test Model.publish
    """
    resp = Model.publish(
        is_new=True,
        model_name="sdk_test",
        version_meta={"taskId": 746, "iterationId": 158},
        tags=["test"],
    )
    assert resp["_request"] == {
        "isNewModel": True,
        "modelName": "sdk_test",
        "tags": ["test"],
        "versionMeta": {"taskId": 746, "iterationId": 158},
    }
    assert "modelId" in resp["result"]
    assert "versionId" in resp["result"]
    assert "version" in resp["result"]
