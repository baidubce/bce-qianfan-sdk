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


from qianfan.resources import FineTune


def test_create_finetune_task():
    """
    test FineTune.create_task
    """
    resp = FineTune.create_task(
        name="test_name_1", base_train_type="base_train_type", train_type="train_type"
    )
    assert resp["_request"] == {
        "name": "test_name_1",
        "baseTrainType": "base_train_type",
        "trainType": "train_type",
    }
    result = resp["result"]
    assert result["name"] == "test_name_1"
    assert result["description"] == ""

    resp = FineTune.create_task(
        name="test_name_2",
        base_train_type="base_train_type",
        train_type="train_type",
        description="test_description",
    )
    assert resp["_request"] == {
        "name": "test_name_2",
        "description": "test_description",
        "baseTrainType": "base_train_type",
        "trainType": "train_type",
    }
    result = resp["result"]
    assert result["name"] == "test_name_2"
    assert result["description"] == "test_description"


def test_create_finetune_job():
    """
    test FineTune.create_job
    """
    req = {
        "taskId": 9167,
        "baseTrainType": "ERNIE-Bot-turbo",
        "trainType": "ERNIE-Bot-turbo-0725",
        "trainMode": "SFT",
        "peftType": "ALL",
        "trainConfig": {"epoch": 1, "learningRate": 0.00003, "maxSeqLen": 4096},
        "trainset": [{"type": 1, "id": 12563}],
        "trainsetRate": 20,
    }
    resp = FineTune.create_job(req)
    assert resp["_request"] == req
    assert "id" in resp["result"]


def test_get_finetune_job():
    """
    test FineTune.create_job
    """
    resp = FineTune.get_job(task_id=123, job_id=456)
    assert resp["_request"] == {"taskId": 123, "jobId": 456}
    assert "id" in resp["result"]
    assert "finishTime" in resp["result"]
    assert "log_id" in resp
    assert "trainMode" in resp["result"]


def test_stop_finetune_job():
    """
    test FineTune.stop_job
    """
    resp = FineTune.stop_job(task_id=147, job_id=258)
    assert resp["_request"] == {"taskId": 147, "jobId": 258}
    assert "result" in resp
