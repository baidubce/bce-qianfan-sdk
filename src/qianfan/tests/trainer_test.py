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
from qianfan.dataset import Dataset, QianfanDataSource
from qianfan.resources.console import consts as console_consts
from qianfan.trainer.actions import (
    DeployAction,
    LoadDataSetAction,
    ModelPublishAction,
    TrainAction,
)
from qianfan.trainer.configs import DeployConfig, TrainConfig
from qianfan.trainer.consts import PeftType, ServiceType
from qianfan.trainer.event import Event, EventHandler
from qianfan.trainer.finetune import LLMFinetune
from qianfan.trainer.model import Model, Service


class MyEventHandler(EventHandler):
    events: list = []

    def dispatch(self, event: Event) -> None:
        print("receive:<", event)
        self.events.append(event)


def test_load_data_action():
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "test", console_consts.DataTemplateType.NonSortedConversation
    )
    ds = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)

    res = LoadDataSetAction(ds).exec(input={"dataset_id": 123})
    assert isinstance(res, dict)
    assert "datasets" in res


def test_train_action():
    ds_id = 111
    ta = TrainAction("ERNIE-Bot-turbo-0725")

    output = ta.exec(
        input={
            "datasets": [
                {"type": console_consts.TrainDatasetType.Platform.value, "id": ds_id}
            ]
        }
    )
    assert isinstance(output, dict)
    assert "task_id" in output and "job_id" in output


def test_model_publish_action():
    publish_action = ModelPublishAction()

    output = publish_action.exec(input={"task_id": 47923, "job_id": 33512})
    assert isinstance(output, dict)
    assert "model_version_id" in output and "model_id" in output


def test_service_deploy_action():
    deploy_config = DeployConfig(replicas=1, pool_type=1, service_type=ServiceType.Chat)
    deploy_action = DeployAction(deploy_config=deploy_config)

    output = deploy_action.exec(
        input={"task_id": 47923, "job_id": 33512, "model_id": 1, "model_version_id": 39}
    )
    assert isinstance(output, dict)
    assert "service_id" in output and "service_endpoint" in output


def test_trainer_sft_run():
    train_config = TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.00002,
        max_seq_len=4096,
        trainset_rate=20,
        peft_type=PeftType.ALL,
    )
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "test", console_consts.DataTemplateType.NonSortedConversation
    )
    ds = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)

    eh = MyEventHandler()
    sft_task = LLMFinetune(
        train_type="ERNIE-Bot-turbo-0725",
        dataset=ds,
        train_config=train_config,
        event_handler=eh,
    )
    sft_task.run()
    res = sft_task.result
    assert res is not None
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0], dict)
    assert "model_version_id" in res[0]
    assert len(eh.events) > 0


def test_trainer_sft_with_deploy():
    train_config = TrainConfig(
        epoch=1, batch_size=4, learning_rate=0.00002, max_seq_len=4096
    )
    deploy_config = DeployConfig(replicas=1, pool_type=1, service_type=ServiceType.Chat)
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "test", console_consts.DataTemplateType.NonSortedConversation
    )
    ds = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)

    eh = MyEventHandler()
    sft_task = LLMFinetune(
        train_type="Llama-2-7b",
        dataset=ds,
        train_config=train_config,
        deploy_config=deploy_config,
        event_handler=eh,
    )
    sft_task.run()
    res = sft_task.result
    assert res is not None
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0], dict)
    assert "service_endpoint" in res[0]
    assert len(eh.events) > 0
    svc = res[0]["service"]
    resp = svc.exec({"messages": [{"content": "hi", "role": "user"}]})
    assert resp["result"] != ""


def test_model_deploy():
    svc = Model(id=1, version_id=1).deploy(
        DeployConfig(replicas=1, pool_type=1, service_type=ServiceType.Chat)
    )

    resp = svc.exec({"messages": [{"content": "hi", "role": "user"}]})
    assert resp["result"] != ""


def test_service():
    svc = Service(model="ERNIE-Bot", service_type=ServiceType.Chat)
    resp = svc.exec({"messages": [{"content": "hi", "role": "user"}]})
    assert resp is not None
    assert resp["result"] != ""


def test_trainer_resume():
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        name="test", template_type=console_consts.DataTemplateType.NonSortedConversation
    )
    ds = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)

    sft_task = LLMFinetune(
        train_type="ERNIE-Bot-turbo-0725",
        dataset=ds,
    )
    ppl = sft_task.ppls[0]

    # 构造一个中断的训练任务
    for k, ac in ppl.actions.items():
        if ac.__class__.__name__ == TrainAction.__name__:
            train_action_key = k
            ac.task_id = 112
            ac.job_id = 123
    ppl._state = train_action_key
    sft_task.resume()
    res = sft_task.result
    assert res is not None
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0], dict)
    assert "model_version_id" in res[0]


def test_batch_run_on_qianfan():
    source = QianfanDataSource.get_existed_dataset(12, False)
    origin_dataset = Dataset.load(source)

    model = Model(1, 2)
    result_dataset = model.batch_inference(origin_dataset, is_download_to_local=False)

    inner_source = result_dataset.inner_data_source_cache
    assert isinstance(inner_source, QianfanDataSource)
    assert inner_source.id == 1
    assert inner_source.group_id == 14510
