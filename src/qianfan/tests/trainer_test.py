from qianfan.trainer.configs import DeployConfig, TrainConfig
from qianfan.trainer.event import Event, EventHandler
from qianfan.trainer.finetune import LLMFinetune


class MyEventHandler(EventHandler):
    def dispatch(self, event: Event) -> None:
        # return super().dispatch(event)
        print("event: ", event)


def test_trainer_sft_start():
    train_config = TrainConfig(
        epoch=1, batch_size=4, learning_rate=0.00002, max_seq_length=4096
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
    assert sft_task.result is not None
    assert isinstance(sft_task.result, dict)
    assert "model_version_id" in sft_task.result


def test_trainer_sft_with_deploy():
    train_config = TrainConfig(
        epoch=1, batch_size=4, learning_rate=0.00002, max_seq_length=4096
    )
    deploy_config = DeployConfig(name="")
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
    print("sft task", sft_task.result)
    res = sft_task.result
    assert sft_task.result is not None
    assert isinstance(sft_task.result, dict)
    assert "model_endpoint" in sft_task.result