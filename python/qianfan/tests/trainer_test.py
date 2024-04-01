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
import os

import pytest

from qianfan.dataset import Dataset
from qianfan.dataset.data_source import QianfanDataSource
from qianfan.errors import InternalError, InvalidArgumentError
from qianfan.evaluation.evaluator import (
    QianfanRefereeEvaluator,
    QianfanRuleEvaluator,
)
from qianfan.model import DeployConfig, Model, Service
from qianfan.model.consts import ServiceType
from qianfan.resources.console import consts as console_consts
from qianfan.trainer.actions import (
    DeployAction,
    EvaluateAction,
    LoadDataSetAction,
    ModelPublishAction,
    TrainAction,
)
from qianfan.trainer.configs import TrainConfig, TrainLimit
from qianfan.trainer.consts import PeftType
from qianfan.trainer.event import Event, EventHandler
from qianfan.trainer.finetune import Finetune, LLMFinetune
from qianfan.trainer.post_pretrain import PostPreTrain


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

    res = LoadDataSetAction(ds).exec()
    assert isinstance(res, dict)
    assert "datasets" in res

    preset = Dataset.load(qianfan_dataset_id="ds-9cetiuhvnbn4mqs3")

    res = LoadDataSetAction(
        preset, dataset_template=console_consts.DataTemplateType.NonSortedConversation
    ).exec()
    assert isinstance(res, dict)
    assert "datasets" in res


def test_train_action():
    ta = TrainAction(
        train_type="ERNIE-Speed", train_mode=console_consts.TrainMode.PostPretrain
    )

    output = ta.exec(
        input={
            "datasets": {
                "sourceType": console_consts.TrainDatasetSourceType.PrivateBos.value,
                "versions": [{"versionBosUri": "bos:/aaa/"}],
            }
        }
    )
    assert isinstance(output, dict)
    assert "task_id" in output and "job_id" in output
    assert isinstance(output["task_id"], str) and output["task_id"] != ""


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


def test_trainer_sft_run_from_bos():
    with pytest.raises(InvalidArgumentError):
        sft_task = LLMFinetune(
            train_type="ERNIE-Bot-turbo-0725",
        )
        sft_task.run()
    sft_task = LLMFinetune(
        train_type="ERNIE-Bot-turbo-0725", dataset_bos_path="bos:/sdk-test/"
    )
    sft_task.run()
    res = sft_task.result
    assert res is not None
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0], dict)
    assert "model_version_id" in res[0]


def test_trainer_sft_with_deploy():
    train_config = TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.00002,
        max_seq_len=4096,
        peft_type=PeftType.ALL,
    )
    deploy_config = DeployConfig(replicas=1, pool_type=1, service_type=ServiceType.Chat)
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "test", console_consts.DataTemplateType.NonSortedConversation
    )
    ds = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)

    eh = MyEventHandler()
    sft_task = LLMFinetune(
        train_type="Qianfan-Chinese-Llama-2-7B",
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
    svc = Model(id="1", version_id="1").deploy(
        DeployConfig(replicas=1, pool_type=1, service_type=ServiceType.Chat)
    )

    resp = svc.exec({"messages": [{"content": "hi", "role": "user"}]})
    assert resp["result"] != ""


def test_service_exec():
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
    ppl.current_action = train_action_key
    sft_task.resume()
    res = sft_task.result
    assert res is not None
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0], dict)
    assert "model_version_id" in res[0]


def test_batch_run_on_qianfan():
    source = QianfanDataSource.get_existed_dataset("12", False)
    origin_dataset = Dataset.load(source)

    model = Model("1", "2")
    result_dataset = model.batch_inference(origin_dataset, output_prettified=False)

    inner_source = result_dataset.inner_data_source_cache
    assert isinstance(inner_source, QianfanDataSource)
    assert inner_source.id == "1"


# 测试_parse_from_input方法
def test__parse_from_input():
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "eval", console_consts.DataTemplateType.NonSortedConversation
    )
    test_dataset = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)
    test_evaluators = [QianfanRuleEvaluator(using_accuracy=True)]  # 创建一些评估器
    action = EvaluateAction(test_dataset, test_evaluators)
    input = {"model": Model("17000", "12333")}
    result = action._parse_from_input(input)
    assert isinstance(result, Model)
    assert result.id == "17000"
    assert result.version_id == "12333"
    input = {"service": Service(model="ERNIE-Bot")}
    result = action._parse_from_input(input)
    assert isinstance(
        result, Service
    )  # 服务对象也可以被解析为模型对象，这里假设Model类有一个从服务对象解析的方法
    input = {"model_id": "17001", "model_version_id": "12666"}
    result = action._parse_from_input(input)
    assert isinstance(result, Model)
    assert result.id == "17001"
    assert result.version_id == "12666"
    input = {}
    with pytest.raises(InvalidArgumentError):
        action._parse_from_input(input)


# 测试eval action exec方法
def test_eval_action_exec():
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "eval", console_consts.DataTemplateType.NonSortedConversation
    )
    test_dataset = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)
    test_evaluators = [QianfanRuleEvaluator(using_similarity=True)]  # 创建一些评估器
    action = EvaluateAction(test_dataset, test_evaluators)
    input = {"model": Model("17002", "12444")}
    result = action.exec(input=input)
    assert (
        result["eval_res"] is not None
    )  # 假设eval_res不为None，具体内容需要根据实际情况进行断言
    result.pop("eval_res")
    assert input == result  # 断言输入数据被保留在结果中


# 测试eval action resume方法
def test_eval_action_resume():
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "eval", console_consts.DataTemplateType.NonSortedConversation
    )
    test_dataset = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)
    test_evaluators = [QianfanRuleEvaluator(using_similarity=True)]  # 创建一些评估器
    action = EvaluateAction(test_dataset, test_evaluators)
    action._input = {"model": Model("17002", "12444")}
    result = action.resume()
    assert (
        result["eval_res"] is not None
    )  # 假设eval_res不为None，具体内容需要根据实际情况进行断言


def test_trainer_sft_with_eval():
    train_config = TrainConfig(
        epoch=1,
        learning_rate=0.00003,
        max_seq_len=4096,
        trainset_rate=20,
        peft_type=PeftType.ALL,
    )
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "train", console_consts.DataTemplateType.NonSortedConversation
    )
    ds = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)
    qianfan_eval_data_source = QianfanDataSource.create_bare_dataset(
        "eval", console_consts.DataTemplateType.NonSortedConversation
    )
    eval_ds = Dataset.load(source=qianfan_eval_data_source, organize_data_as_group=True)
    eh = MyEventHandler()
    sft_task = LLMFinetune(
        train_type="ERNIE-Speed",
        dataset=ds,
        train_config=train_config,
        event_handler=eh,
        eval_dataset=eval_ds,
        evaluators=[QianfanRefereeEvaluator(app_id=18890)],
    )
    sft_task.run()
    res = sft_task.result
    assert res is not None
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0], dict)
    assert "model_version_id" in res[0]
    assert len(eh.events) > 0
    assert res[0].get("eval_res") is not None


def test_train_config_load():
    # 使用 patch 和 mock_open 来模拟文件
    yaml_config_path = "config.yaml"
    json_config_path = "config.json"

    try:
        with open(yaml_config_path, mode="w") as f:
            f.write("""
                    epoch: 1
                    batch_size: 4
                    max_seq_len: 4096
                """)

        with open(json_config_path, mode="w") as f:
            f.write("""
                {
                    "epoch": 1,
                    "batch_size": 4,
                    "max_seq_len": 4096
                }
                """)

        tc = TrainConfig.load(yaml_config_path)
        assert tc.epoch == 1
        assert tc.batch_size == 4
        assert tc.max_seq_len == 4096

        tc = TrainConfig.load(json_config_path)
        assert tc.epoch == 1
        assert tc.batch_size == 4
        assert tc.max_seq_len == 4096

    finally:
        os.remove(yaml_config_path)
        os.remove(json_config_path)


def test_train_limit__or__():
    common = TrainLimit(batch_size_limit=(1, 4), epoch_limit=(1, 2))
    specific = TrainLimit(epoch_limit=(1, 3))
    res = specific | common
    assert res.batch_size_limit == (1, 4)
    assert res.epoch_limit == (1, 3)


def test_train_config_validate():
    conf = TrainConfig(epoch=4, batch_size=4, max_seq_len=4096, learning_rate=0.0002)
    # 不存在的字段
    res = conf.validate_config(TrainLimit(epoch=(1, 2)))
    assert not res
    res = conf.validate_config(TrainLimit(epoch=(1, 2), batch_size=(1, 20)))
    assert not res
    res = conf.validate_config(
        TrainLimit(
            epoch=(1, 8),
            batch_size=(1, 10),
            max_seq_len=[1024, 2048, 4096],
            learning_rate=(0.000001, 0.1),
        )
    )
    assert res


def test_ppt():
    ppt_ds = Dataset.load(qianfan_dataset_id="ds-mock-generic")
    ppt_trainer = PostPreTrain(
        train_type="ERNIE-Speed",
        dataset=ppt_ds,
    )
    ppt_trainer.run()
    res = ppt_trainer.output
    assert "task_id" in res and "job_id" in res


def test_ppt_with_sft():
    ppt_ds = Dataset.load(qianfan_dataset_id="ds-mock-generic")
    ppt_trainer = PostPreTrain(
        train_type="ERNIE-Speed",
        dataset=ppt_ds,
    )
    ppt_trainer.run()
    assert "task_id" in ppt_trainer.output and "job_id" in ppt_trainer.output

    sft_ds = Dataset.load(qianfan_dataset_id="ds-111")
    sft_trainer = LLMFinetune(
        dataset=sft_ds, previous_trainer=ppt_trainer, name="ppt_with_sft"
    )
    sft_trainer.run()
    assert "model_version_id" in sft_trainer.output and "model_id" in sft_trainer.output


def test_all_default_config():
    from qianfan.trainer.configs import (
        DefaultPostPretrainTrainConfigMapping,
        DefaultTrainConfigMapping,
    )

    sft_ds = Dataset.load(qianfan_dataset_id="ds-111")

    for k in DefaultTrainConfigMapping.keys():
        LLMFinetune(
            train_type=k,
            dataset=sft_ds,
        )

    ppt_ds = Dataset.load(qianfan_dataset_id="ds-mock-generic")
    for k in DefaultPostPretrainTrainConfigMapping.keys():
        PostPreTrain(
            train_type=k,
            dataset=ppt_ds,
        )


def test_failed_sft_run():
    train_config = TrainConfig(
        epoch=1,
        learning_rate=0.00003,
        max_seq_len=4096,
        trainset_rate=20,
        peft_type=PeftType.ALL,
    )
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "test", console_consts.DataTemplateType.NonSortedConversation
    )
    ds = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)

    sft_task = LLMFinetune(
        train_type="ERNIE-Speed",
        dataset=ds,
        train_config=train_config,
        name="mock_failed_task",
    )
    with pytest.raises(InternalError):
        sft_task.run()
    assert "error" in sft_task.output


def test_increment_sft():
    sft_ds = Dataset.load(qianfan_dataset_id="ds-111")
    trainer = LLMFinetune(
        dataset=sft_ds,
        previous_task_id="task-abc",
    )
    trainer.run()
    res = trainer.output
    assert res is not None
    assert isinstance(res, dict)
    assert "model_version_id" in res


def test_persist():
    train_config = TrainConfig(
        epoch=1,
        learning_rate=0.00002,
        max_seq_len=4096,
        trainset_rate=20,
        peft_type=PeftType.ALL,
    )
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "test", console_consts.DataTemplateType.NonSortedConversation
    )
    ds = Dataset.load(source=qianfan_data_source, organize_data_as_group=True)

    trainer = LLMFinetune(
        train_type="ERNIE-Speed",
        dataset=ds,
        train_config=train_config,
    )
    trainer.run()

    trainers = Finetune.list()
    assert len(trainers) >= 1

    pre_id = trainers[0].id
    sft = Finetune.load(pre_id)
    assert sft.info().get("id") == pre_id
