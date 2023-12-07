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


def test_create_evaluation_task():
    """
    test Model.create_evaluation_task
    """
    resp = Model.create_evaluation_task(
        name="test_name",
        version_info=[{"modelId": 12, "modelVersionId": 34}],
        dataset_id=123,
        eval_config={
            "evalMode": "model,manual",
            "appId": 1234,
            "prompt": {
                "templateContent": "?",
                "metric": "no",
                "steps": "steps",
                "maxScore": 12,
            },
            "evaluationDimension": [
                {
                    "dimension": "dimension",
                    "description": "description",
                }
            ],
        },
    )

    request = resp["_request"]
    assert request["name"] == "test_name"


def test_get_evaluation_info():
    """
    test Model.get_evaluation_info
    """

    resp = Model.get_evaluation_info(
        123,
    )

    assert resp["_request"]["id"] == 123


def test_get_evaluation_result():
    """
    test Model.get_evaluation_result
    """

    resp = Model.get_evaluation_result(
        123,
    )

    assert resp["_request"]["id"] == 123


def test_stop_evaluation_task():
    """
    test Model.stop_evaluation_task
    """

    resp = Model.stop_evaluation_task(
        123,
    )

    assert resp["_request"]["id"] == 123
