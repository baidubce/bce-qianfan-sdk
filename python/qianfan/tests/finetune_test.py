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
from qianfan.resources.console import consts as console_consts


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
        "peftType": console_consts.TrainParameterScale.FullFineTuning,
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


def test_finetune_v2_create_job():
    resp = FineTune.V2.create_job(name="hiii", model="ERNIE-Speed", train_mode="SFT")
    assert resp["_request"]["name"] == "hiii"
    assert resp["_request"]["model"] == "ERNIE-Speed"
    assert "result" in resp


def test_finetune_v2_create_task():
    from qianfan.resources.console.consts import TrainParameterScale

    job_id = "job-xx1234"
    resp = FineTune.V2.create_task(
        job_id=job_id,
        params_scale=TrainParameterScale.FullFineTuning,
        hyper_params={
            "learning_rate": 0.0001,
            "epoch": 1,
        },
        dataset_config={
            "sourceType": "Platform",
            "corpusProportion": "1:5",
            "datasets": [{"datasetId": "ds-p1t2wiv12f1vwsch"}],
            "splitRatio": 20,
        },
    )
    assert resp["result"]["jobId"] == job_id
    assert resp["result"]["taskId"] != ""


def test_finetune_v2_task_detail():
    task_id = "task-xx1234"
    resp = FineTune.V2.task_detail(task_id=task_id)
    assert resp["result"]["taskId"] == task_id


def test_finetune_v2_job_list():
    resp = FineTune.V2.job_list()
    assert "pageInfo" in resp["result"]
    assert len(resp["result"]["jobList"]) > 0


def test_finetune_v2_task_list():
    job_id = "job-xx1234"
    resp = FineTune.V2.task_list(job_id=job_id)
    assert "pageInfo" in resp["result"]
    assert len(resp["result"]["taskList"]) > 0
    assert resp["result"]["taskList"][0]["jobId"] == job_id


def test_finetune_v2_stop_task():
    resp = FineTune.V2.stop_task(task_id="NoExistedId")
    assert not resp["result"]
    resp = FineTune.V2.create_job(
        name="teststop", model="ERNIE-Speed", train_mode="SFT"
    )
    job_id = resp["result"]["jobId"]
    resp = FineTune.V2.create_task(
        job_id=job_id,
        params_scale=console_consts.TrainParameterScale.FullFineTuning,
        hyper_params={
            "learning_rate": 0.0001,
            "epoch": 1,
        },
        dataset_config={
            "sourceType": "Platform",
            "corpusProportion": "1:5",
            "datasets": [{"datasetId": "ds-p1t2wiv12f1vwsch"}],
            "splitRatio": 20,
        },
    )
    assert resp["result"]["jobId"] == job_id
    assert resp["result"]["taskId"] != ""
    task_id = resp["result"]["taskId"]
    resp = FineTune.V2.stop_task(task_id=task_id)
    assert resp["result"]


def test_finetune_v2_supported_models():
    resp = FineTune.V2.supported_models()
    assert len(resp["result"]) == 1
    assert resp["result"][0]["model"]
    assert resp["result"][0]["modelType"]
    assert resp["result"][0]["supportTrainMode"]
