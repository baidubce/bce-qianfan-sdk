from qianfan.resources.console import consts as console_consts
from qianfan.trainer.consts import ServiceType
from qianfan.trainer.configs import DeployConfig, TrainConfig
from qianfan.trainer.event import Event, EventHandler
from qianfan.trainer.finetune import (
    DeployAction,
    LLMFinetune,
    ModelPublishAction,
    TrainAction,
)


class MyEventHandler(EventHandler):
    events: list = []

    def dispatch(self, event: Event) -> None:
        print("receive:<", event)
        self.events.append(event)


def test_train_action():
    ds_id = 111
    ta = TrainAction("ERNIE-Bot-turbo-0725")

    output = ta.exec(
        {
            "datasets": [
                {"type": console_consts.TrainDatasetType.Platform.value, "id": ds_id}
            ]
        }
    )
    assert isinstance(output, dict)
    assert "task_id" in output and "job_id" in output


def test_model_publish_action():
    publish_action = ModelPublishAction()

    output = publish_action.exec({"task_id": 47923, "job_id": 33512})
    assert isinstance(output, dict)
    assert "model_version_id" in output and "model_id" in output


def test_service_deploy_action():
    deploy_config = DeployConfig(replicas=1, pool_type=1, service_type=ServiceType.Chat)
    deploy_action = DeployAction(deploy_config=deploy_config)

    output = deploy_action.exec(
        {"task_id": 47923, "job_id": 33512, "model_id": 1, "model_version_id": 39}
    )
    assert isinstance(output, dict)
    assert "service_id" in output and "service_endpoint" in output


def test_trainer_sft_start():
    train_config = TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.00002,
        max_seq_len=4096,
        trainset_rate=20,
    )
    ds_id = 111

    eh = MyEventHandler()
    sft_task = LLMFinetune(
        model_version_type="ERNIE-Bot-turbo-0725",
        dataset={"datasets": [{"type": 1, "id": ds_id}]},
        train_config=train_config,
        event_handler=eh,
    )
    sft_task.start()
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
    ds_id = 111
    train_config.model_dump_json()

    eh = MyEventHandler()
    sft_task = LLMFinetune(
        model_version_type="ERNIE-Bot-turbo-0725",
        dataset={"datasets": [{"type": 1, "id": ds_id}]},
        train_config=train_config,
        deploy_config=deploy_config,
        event_handler=eh,
    )
    sft_task.start()
    res = sft_task.result
    assert res is not None
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0], dict)
    assert "service_endpoint" in res[0]
    assert len(eh.events) > 0
