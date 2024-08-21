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
import copy
import time
from typing import Any, Dict, List, Optional, Union, cast

from qianfan import resources as api
from qianfan.config import get_config
from qianfan.dataset import BosDataSource, Dataset, QianfanDataSource
from qianfan.dataset.data_source import DataSource
from qianfan.errors import InternalError, InvalidArgumentError
from qianfan.evaluation import EvaluationManager
from qianfan.evaluation.evaluator import Evaluator, LocalEvaluator, QianfanEvaluator
from qianfan.model import Model, Service
from qianfan.model.configs import DeployConfig
from qianfan.resources.console import consts as console_consts
from qianfan.trainer.base import (
    ActionState,
    BaseAction,
    with_event,
)
from qianfan.trainer.configs import (
    CorpusConfig,
    CorpusConfigItem,
    DatasetConfig,
    PeftType,
    TrainConfig,
    TrainLimit,
    get_default_train_config,
    get_model_info,
)
from qianfan.trainer.consts import ServiceStatus, TrainStatus
from qianfan.utils import (
    bos_uploader,
    log_debug,
    log_error,
    log_info,
    log_warn,
    utils,
)
from qianfan.utils.bos_uploader import is_valid_bos_path, parse_bos_path
from qianfan.utils.utils import first_lower_case, snake_to_camel


class LoadDataSetAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """LoadDataSetAction
    Action for dataset's loading, invokes the dataset's save method
    to guarantee the dataset is loaded in Qianfan platform.
    Sample:
        ```
        load_action = LoadDataSetAction(dataset=Dataset(id=1))
        load_action.exec()
        ```

    input:
        none
    output:
        ```
            {
                "datasets": {
                "sourceType": (
                   2
                ),
                "versions": [
                        {
                            "versionBosUri": "bos:/bbb/"
                        }
                    ],
                }
            }
        ```
    """

    datasets: List[Union[DataSource, Dict]] = []
    sampling_rates: List[float] = []
    result: Optional[Dict[str, Any]] = None
    eval_split_ratio: Optional[float] = None
    corpus_config: Optional[CorpusConfig] = None
    source_type: Optional[console_consts.TrainDatasetSourceType] = None

    def __init__(
        self,
        dataset: Union[DatasetConfig, Dataset, str, List[str]],
        dataset_template: Optional[console_consts.DataTemplateType] = None,
        corpus_config: Optional[CorpusConfig] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.eval_split_ratio = kwargs.get("eval_split_ratio", 20)

        global_sampling_rate = kwargs.get("sampling_rate")
        if kwargs.get("corpus_type"):
            self.corpus_config = CorpusConfig()
            self.corpus_config.corpus_configs.append(CorpusConfigItem(**kwargs))
        if isinstance(dataset, str):
            dataset = [dataset]

        if isinstance(dataset, DatasetConfig):
            global_sampling_rate = global_sampling_rate or dataset.sampling_rate
            if isinstance(dataset.datasets[0], Dataset):
                self.datasets = [ds.inner_data_source_cache for ds in dataset.datasets]
            elif isinstance(dataset.datasets[0], DataSource):
                self.datasets = dataset.datasets
            elif isinstance(dataset.datasets[0], dict):
                self.datasets = dataset.datasets
            if dataset.sampling_rates:
                self.sampling_rates = dataset.sampling_rates
            if self.corpus_config is None:
                self.corpus_config = CorpusConfig()
            if dataset.corpus_type:
                self.corpus_config.corpus_configs.append(
                    CorpusConfigItem(  # type:ignore
                        corpus_proportion=dataset.corpus_proportion,
                        corpus_type=dataset.corpus_type,
                        corpus_labels=dataset.corpus_labels,
                    )
                )
            if dataset.eval_split_ratio is not None:
                self.eval_split_ratio = dataset.eval_split_ratio

            if dataset.sampling_rates is None and global_sampling_rate:
                self.sampling_rates = [
                    global_sampling_rate for i in range(len(self.datasets))
                ]
            if self.sampling_rates and len(self.datasets) != len(self.sampling_rates):
                raise ValueError("sampling_rates not with the same counts to datasets")
            if dataset.source_type:
                self.source_type = console_consts.TrainDatasetSourceType(
                    dataset.source_type
                )
        elif isinstance(dataset, list):
            if len(dataset) > 0:
                if isinstance(dataset[0], str):
                    for ds_str in dataset:
                        if is_valid_bos_path(ds_str):
                            bos_ds_src = LoadDataSetAction.create_bos_ds_src(ds_str)
                            self.datasets.append(bos_ds_src)
                        elif ds_str.startswith("ds-"):
                            self.datasets.append(
                                QianfanDataSource.get_existed_dataset(ds_str)
                            )
                        else:
                            raise InvalidArgumentError(f"invalid dataset_str: {ds_str}")
                elif isinstance(dataset[0], Dataset):
                    self.datasets = dataset
        elif isinstance(dataset.inner_data_source_cache, QianfanDataSource):
            qf_data_src = cast(QianfanDataSource, dataset.inner_data_source_cache)
            if (
                dataset_template is not None
                and qf_data_src.template_type != dataset_template
            ):
                raise InvalidArgumentError(
                    f"dataset must be `{dataset_template}` template."
                )
            self.datasets = [dataset.inner_data_source_cache]
        elif isinstance(dataset.inner_data_source_cache, BosDataSource):
            self.datasets = [dataset.inner_data_source_cache]
        else:
            raise InvalidArgumentError(
                "dataset must be either implemented with QianfanDataSource or"
                " BosDataSource or a bos path"
            )
        if global_sampling_rate and self.sampling_rates is None:
            self.sampling_rates = [
                global_sampling_rate for i in range(len(self.datasets))
            ]
        if corpus_config is not None:
            self.corpus_config = corpus_config

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        resp = self._exec(input, **kwargs)
        if resp.get("datasets") is None:
            return resp
        if self.eval_split_ratio is not None:
            resp["datasets"]["splitRatio"] = self.eval_split_ratio
        if self.corpus_config and len(self.corpus_config.corpus_configs) > 0:
            resp["corpus_config"] = self.corpus_config.dict(
                by_alias=True, exclude_none=True
            )
        if self.sampling_rates:
            for i, d in enumerate(resp["datasets"]["versions"]):
                d["samplingRate"] = self.sampling_rates[i]
        return resp

    def _exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        """
        Load dataset implementation, may called by exec and resume.
        """
        result = self.get_action_result(**kwargs)
        if len(result["datasets"]["versions"]) == 0:
            raise InvalidArgumentError(
                "dataset must be set or input dataset is invalid"
            )
        self.result = result
        return result

    def get_action_result(self, **kwargs: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        versions: List[Dict[str, Any]] = []
        for i, dataset in enumerate(self.datasets):
            if isinstance(dataset, Dict):
                version = dataset
            elif isinstance(dataset, DataSource):
                sub_res = self.get_dataset_result(dataset, **kwargs)
                if sub_res is None:
                    log_warn(f"invalid dataset {dataset}")
                    continue
                if result.get("sourceType") and sub_res.get("sourceType") != result.get(
                    "sourceType"
                ):
                    log_warn(
                        "[load_dataset_action] dataset sourceType conflict, should all"
                        f" be with one source type{sub_res}"
                    )
                else:
                    self.source_type = sub_res.get("sourceType")
                version = sub_res.get("version", {})
            if self.sampling_rates:
                version["samplingRate"] = self.sampling_rates[i]
            if isinstance(version, dict):
                versions.append(version)

        result["versions"] = versions
        if self.source_type:
            result["sourceType"] = self.source_type.value
        else:
            log_error(
                "[load_dataset_action] dataset dict must be set with"
                " DatasetConfig.source_type"
            )
            raise InvalidArgumentError("dataset dict must be set with source_type")
        return {"datasets": result}

    def get_dataset_result(
        self,
        data_src: DataSource,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        from qianfan.dataset.data_source import BosDataSource, QianfanDataSource

        if isinstance(data_src, QianfanDataSource):
            log_debug("[load_dataset_action] prepare train-set")
            qf_data_src = cast(QianfanDataSource, data_src)
            is_released = qf_data_src.release_dataset(**kwargs)
            if not is_released:
                log_error("[load_dataset_action] dataset not released")
                raise InvalidArgumentError("dataset must be released")
            log_debug("[load_dataset_action] dataset loaded successfully")
            return {
                "sourceType": console_consts.TrainDatasetSourceType.Platform,
                "version": {
                    "versionId": qf_data_src.id,
                },
            }
        elif isinstance(data_src, BosDataSource):
            log_debug("[load_dataset_action] prepare train-set in BOS")
            bos_data_src = cast(BosDataSource, data_src)
            return {
                "sourceType": console_consts.TrainDatasetSourceType.PrivateBos,
                "version": {
                    "versionBosUri": bos_uploader.generate_bos_file_path(
                        bos_data_src.bucket, bos_data_src.bos_file_path
                    )
                },
            }
        else:
            return None

    @staticmethod
    def create_bos_ds_src(bos_uri: str) -> BosDataSource:
        bucket, bos_path = parse_bos_path(bos_uri)
        return BosDataSource(
            region=get_config().BOS_HOST_REGION,
            bucket=bucket,
            bos_file_path=bos_path,
        )

    @staticmethod
    def get_data_src_from_action_result(
        dataset_result: Dict[str, Any]
    ) -> List[DataSource]:
        res = []
        dataset_src_type = dataset_result.get("sourceType")
        for ds_dict in dataset_result.get("versions", []):
            if dataset_src_type == console_consts.TrainDatasetSourceType.Platform.value:
                ds = Dataset.load(qianfan_dataset_id=ds_dict.get("versionId"))
                if ds.inner_data_source_cache:
                    res.append(
                        ds.inner_data_source_cache,
                    )
            elif (
                dataset_src_type
                == console_consts.TrainDatasetSourceType.PrivateBos.value
            ):
                bos_ds_src = LoadDataSetAction.create_bos_ds_src(
                    ds_dict.get("versionBosUri")
                )
                res.append(bos_ds_src)
            elif (
                dataset_src_type
                == console_consts.TrainDatasetSourceType.PrivateAfs.value
            ):
                continue
            else:
                log_warn("[load_dataset_action] invalid dataset source: {ds_dict}")
        return res

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        """
        resume method for load dataset action.

        Returns:
            Dict[str, Any]: datasets meta_info including
            dataset_id and dataset_type.
        """
        log_debug("[load_dataset_action] dataset loading resumed")
        return self._exec(**kwargs)

    def persist(self) -> bytes:
        return self.serialize_helper.serialize(self._action_dict())

    def _action_dict(self) -> Dict[str, Any]:
        meta = {
            "id": self.id,
            "type": LoadDataSetAction.__name__,
            "datasets": self.get_action_result().get("datasets"),
            "output": self.result,
            "eval_split_ratio": self.eval_split_ratio,
        }
        if self.corpus_config:
            meta["corpus_config"] = self.corpus_config.dict(
                by_alias=True, exclude_none=True
            )
        return meta

    @classmethod
    def _load_from_dict(cls, meta: Dict[str, Any]) -> "LoadDataSetAction":
        init_params: Dict[str, Any] = {}
        if meta.get("datasets") or meta.get("output"):
            ds_dicts = meta.get("datasets")
            if ds_dicts is None:
                ds_output = meta.get("output")
                assert isinstance(ds_output, dict)
                ds_dicts = ds_output.get("datasets")
            assert isinstance(ds_dicts, dict)
            datasets = LoadDataSetAction.get_data_src_from_action_result(ds_dicts)
            corpus_config_meta = meta.get("corpus_config")
            init_params["dataset"] = DatasetConfig(datasets=datasets)
            if corpus_config_meta:
                init_params["corpus_config"] = CorpusConfig.parse_obj(
                    corpus_config_meta
                )
            if meta.get("id"):
                init_params["id"] = meta.get("id")
            if meta.get("eval_split_ratio"):
                init_params["dataset"].eval_split_ratio = meta.get("eval_split_ratio")
        else:
            log_error(f"unknown load_dataset_action: {meta}")
            raise ValueError("unknown action meta")
        action = cls(
            **init_params,
        )
        action.result = meta.get("output")
        return action

    @classmethod
    def load(cls, b: bytes) -> "LoadDataSetAction":
        meta = cls.serialize_helper.deserialize(b)
        assert isinstance(meta, dict)
        return cls._load_from_dict(meta)


class TrainAction(
    BaseAction[Dict[str, Any], Dict[str, Any]],
):
    """
    Class for Train Action, Synchronous invocation of the training API,
    taking a dataset metadata dict as input and producing a model metadata
    as output. Concretely, `exec` is called for running.

    Note: this action is not involved with model publishing, please use use
    `ModelPublishAction` for publishing model.

    Sample:

    Input:
    ```
        {
            "datasets": {
            "sourceType": (
                2
            ),
            "versions": [
                    {
                        "versionBosUri": "bos:/bbb/"
                    }
                ],
            }
        }
    ```

    Output:
    ```
        {'task_id': "task-ddd", 'job_id': "job-xxxx"}
    ```
    """

    task_id: Optional[str] = None
    """train task id"""
    job_id: Optional[str] = None
    """train job id"""
    train_type: Optional[str] = ""
    """train_type"""
    is_incr: bool = False
    """if it's incremental train or not"""
    _last_task_id: Optional[str] = None
    """last task id"""
    _last_task_step: Optional[int] = None
    """last task step"""
    train_config: Optional[TrainConfig] = None
    """train config"""
    train_mode: console_consts.TrainMode
    """train mode"""
    job_name: str = ""
    """train task name"""
    task_description: Optional[str] = None
    """train task description"""
    job_description: Optional[str] = None
    """train job description"""
    _input: Optional[Dict[str, Any]] = None
    """train input"""
    result: Optional[Dict[str, Any]] = None
    """"train result"""
    train_model_name: Optional[str] = None
    """real name to start training"""
    task_status: Optional[str] = None
    """train task status, e.g. `Running`"""
    progress: Optional[int] = 0
    """training progress 0-100"""
    vdl_link: Optional[str] = None
    """visualdl link"""
    log_link: Optional[str] = None
    """log link"""

    def __init__(
        self,
        train_mode: Union[console_consts.TrainMode, str],
        train_type: Optional[str] = None,
        train_config: Optional[TrainConfig] = None,
        task_id: Optional[str] = None,
        job_id: Optional[str] = None,
        peft_type: Optional[PeftType] = None,
        job_name: Optional[str] = None,
        task_description: Optional[str] = None,
        job_description: Optional[str] = None,
        task_step: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """

        Parameters:
            train_mode Union[console_consts.TrainMode, str]:
                train mode, e.g. `SFT`, `PostPretrain`, `DPO`. Defaults to None.
            train_type (Optional[str], optional):
                train_type, must be specified when it's not increment training
                like 'ERNIE-Speed-8K'
            train_config (Optional[TrainConfig], optional):
                train_config, e.g. `epoch=10, batch_size=32`.
            task_id (Optional[int], optional):
                used in incr train, model train task_id. Defaults to None.
            job_id (Optional[int], optional):
                used in incr train, mod train job_id. Defaults to None.
            peft_type: Optional[PeftType], optional):
                peft_type, e.g. `pretrain`, `finetune`. Defaults to None.
            job_name (Optional[str], optional):
                train task name. Defaults to None.
            task_description (Optional[str], optional):
                train task description. Defaults to None.
            job_description (Optional[str], optional):
                train job description. Defaults to None.
        """
        super().__init__(**kwargs)
        # for persist
        self._init_job_id = job_id
        self._init_task_id = task_id
        self._last_task_id = task_id
        self._last_task_step = task_step
        self.job_id = job_id
        self.train_mode = console_consts.TrainMode(train_mode)
        self.train_model_name = train_type
        if self._last_task_id is not None:
            # if incremental train
            pre_task_detail = api.FineTune.V2.task_detail(task_id=self._last_task_id)
            # 获取增量任务的训练model
            if pre_task_detail.get("result") is not None:
                self.train_type = pre_task_detail["result"]["model"]
                if self.train_mode.value == pre_task_detail["result"]["trainMode"]:
                    self.job_id = pre_task_detail.get("result", {}).get("jobId")
            self.is_incr = True
        else:
            if train_type is None:
                raise InvalidArgumentError("train_type must be specified")
            # 从基础模型开始训练
            self.train_type = train_type
            model_info = get_model_info(self.train_mode, self.train_type)
            if model_info is None:
                log_warn(f"unknown train model type: {self.train_type} is not found")
            elif model_info.model != "":
                # 兼容改名模型
                self.train_model_name = model_info.model
        assert self.train_type is not None
        if train_config is None:
            train_config = self.get_default_train_config(
                self.train_type, self.train_mode, peft_type
            )
        self.train_config = train_config
        self.validateTrainConfig(strict=kwargs.get("validate_strict", True))
        self.job_name = self._generate_job_name(job_name, self.train_type)
        self.task_description = task_description
        self.job_description = job_description

    def _generate_job_name(
        self, job_name: Optional[str], train_type: Optional[str]
    ) -> str:
        if job_name is not None:
            return job_name
        model_info = (
            get_model_info(self.train_mode, train_type)
            if train_type is not None
            else None
        )
        return (
            f"job_{utils.generate_letter_num_random_id()}"
            if model_info is None
            else f"{model_info.short_name}_{utils.generate_letter_num_random_id(5)}"
        )

    def validateTrainConfig(self, strict: bool = True) -> None:
        """
        validate train_config with ModelInfo Limits

        Raises:
            InvalidArgumentError: _description_
        """
        if self.train_config is None:
            raise InvalidArgumentError("none train_config")
        else:
            assert self.train_type
            train_type_model_info = get_model_info(self.train_mode, self.train_type)
            if train_type_model_info is None:
                return
            if (
                self.train_config.peft_type
                not in train_type_model_info.support_peft_types
            ):
                log_warn(
                    f"[train_action] train_type {self.train_type}, peft_type"
                    f" {self.train_config.peft_type} not found, it may be not supported"
                )
                if strict:
                    raise InvalidArgumentError(
                        f"[train_action] train_type {self.train_type}, peft_type"
                        f" {self.train_config.peft_type} not found, it may be not"
                        " supported"
                    )

            else:
                assert train_type_model_info
                res = False
                if (
                    train_type_model_info.specific_peft_types_params_limit is not None
                    and self.train_config.peft_type
                    in train_type_model_info.specific_peft_types_params_limit
                ):
                    res = self._validate_train_config(
                        train_type_model_info.specific_peft_types_params_limit[
                            self.train_config.peft_type
                        ]
                        | train_type_model_info.common_params_limit,
                    )
                else:
                    res = self._validate_train_config(
                        train_type_model_info.common_params_limit
                    )
                if not res and strict:
                    raise InvalidArgumentError(
                        "invalid train_config, please check the config"
                    )

    def _validate_train_config(self, train_limit: TrainLimit) -> bool:
        """
        validate train_config with a specific train_limit

        Args:
            train_limit (TrainLimit): _description_

        Raises:
            InvalidArgumentError: _description_
        """
        if self.train_config is None:
            raise InvalidArgumentError("validate train_config is none")
        return self.train_config.validate_config(train_limit)

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        """
        exec method for train action

        Args:
            input (Dict[str, Any], optional):
                input with dataset meta:
                for example:
                    Input:
                    ```
                    {'datasets':[{'type': 1, 'id': 111}]}
                    ```
        Raises:
            InvalidArgumentError: invalid dataset input

        Returns:
            Dict[str, Any]:
                train task output with task_id and job_id
                for example:
                    Output:
                    ```
                    {'task_id': 47923, 'job_id': 33512}
                    ```
        """
        # for resume
        if self._input is None:
            self._input = input
        return self._exec(self._input, **kwargs)

    def _exec(self, input: Dict[str, Any] = {}, **kwargs: Any) -> Dict[str, Any]:
        # 校验数据集
        ds_config = input.get("datasets")
        if ds_config is None:
            raise InvalidArgumentError("train set must be set")
        assert isinstance(ds_config, dict)
        assert self.train_config

        if not self.job_id:
            # request for create model train task
            assert self.train_type is not None
            resp = api.FineTune.V2.create_job(
                name=self.job_name,
                description=self.task_description,
                model=(
                    self.train_model_name if self.train_model_name else self.train_type
                ),
                train_mode=self.train_mode,
                **kwargs,
            )

            self.job_id = str(resp["result"]["jobId"])
            log_debug(
                f"[train_action] create {self.train_mode} train job: {self.job_id}"
            )

        assert self.train_config is not None
        hyper_params_dict = {
            **self.train_config.dict(
                exclude={"peft_type", "trainset_rate", "extras", "resource_config"}
            ),
            **self.train_config.extras,
        }
        hyper_params_dict = {
            first_lower_case(snake_to_camel(key)): value
            for key, value in hyper_params_dict.items()
            if value is not None
        }
        # custom fix
        if "packing" in hyper_params_dict:
            hyper_params_dict["Packing"] = hyper_params_dict.pop("packing")
        ds_config = input["datasets"]
        log_debug(f"train with ds_config: { ds_config}")
        log_debug(f"train with hyper_params: { hyper_params_dict}")
        if self.is_incr:
            # 增量训练
            kwargs["increment_task_id"] = self._last_task_id
            if self._last_task_step:
                kwargs["increment_checkpoint_step"] = self._last_task_step
            log_info(
                f"train with incrementTaskId: { self._last_task_id} with step:"
                f" { self._last_task_step}"
            )
        assert self.train_config.peft_type is not None
        # 语料混合配置
        if input.get("corpus_config"):
            kwargs["corpus_config"] = input.get("corpus_config")
        # 训练资源配置
        if self.train_config.resource_config:
            kwargs["resource_config"] = self.train_config.resource_config.dict(
                by_alias=True, exclude_none=True
            )
        create_task_resp = api.FineTune.V2.create_task(
            job_id=self.job_id,
            params_scale=self.train_config.peft_type,
            hyper_params=hyper_params_dict,
            dataset_config=ds_config,
            **kwargs,
        )
        self.task_id = str(create_task_resp["result"]["taskId"])
        log_debug(f"[train_action] create {self.train_mode} train task: {self.task_id}")

        # 获取job状态，是否训练完成
        train_output = self._wait_model_trained(**kwargs)
        self.result = {
            **input,
            "task_id": self.task_id,
            "job_id": self.job_id,
            **train_output,
        }
        assert self.result is not None
        return self.result

    def _wait_model_trained(self, **kwargs: Dict) -> Dict[str, Any]:
        if self.task_id is None:
            raise InvalidArgumentError("task_id must not be None")
        output = {}
        while True:
            task_status_resp = api.FineTune.V2.task_detail(
                task_id=self.task_id,
                retry_count=kwargs.get(
                    "retry_count", get_config().TRAINER_STATUS_POLLING_RETRY_TIMES
                ),
                backoff_factor=kwargs.get(
                    "backoff_factor", get_config().TRAINER_STATUS_POLLING_BACKOFF_FACTOR
                ),
            )
            task_status_result = task_status_resp.get("result", {})
            task_status = task_status_result.get("runStatus")
            # 更新任务状态
            self.task_status = task_status

            self.action_event(ActionState.Running, "train running", task_status_resp)
            if task_status == console_consts.TrainStatus.Finish:
                output["metrics"] = task_status_result.get("metrics", {})
                output["checkpoints"] = task_status_result.get("checkpointList", [])
                log_info(f"[train_action] training task metrics: {output['metrics']}")
                log_info(
                    f"[train_action] training task checkpoints: {output['checkpoints']}"
                )
                break
            elif task_status in [
                console_consts.TrainStatus.Fail,
                console_consts.TrainStatus.Stop,
            ]:
                log_error(
                    "[train_action] training job"
                    f" {self.job_id}/{self.task_id} has ended,"
                    f" {task_status_resp}"
                )
                raise InternalError(
                    f"[train_action]training job {self.job_id}/{self.task_id} has ended"
                    f" with status: {task_status}"
                )
            elif task_status == console_consts.TrainStatus.Running:
                job_progress_str = task_status_result.get("runProgress")
                job_progress = int(job_progress_str[:-1])
                self.progress = job_progress
                log_prefix = log_prefix_mapping.get(self.train_mode, "sft")
                self.log_link = f"https://console.bce.baidu.com/qianfan/train/{log_prefix}/{self.job_id}/{self.task_id}/detail/traininglog"
                self.vdl_link = task_status_result.get("vdlLink", "")
                log_info(
                    "[train_action] training ..."
                    f" job_name:{self.job_name} current status: {task_status},"
                    f" {job_progress}% check train task log in"
                    f" {self.log_link}"
                )
                if job_progress >= 50:
                    log_info(f" check vdl report in {self.vdl_link}")
                time.sleep(get_config().TRAIN_STATUS_POLLING_INTERVAL)
            elif task_status == "":
                time.sleep(get_config().TRAIN_STATUS_POLLING_INTERVAL)
            elif task_status == console_consts.TrainStatus.Waiting:
                log_info(f"[train_action] {self.job_id}/{self.task_id} queueing...")
                time.sleep(get_config().TRAIN_STATUS_POLLING_INTERVAL)
            else:
                raise InternalError(
                    f"[train_action] job: {self.job_name} task:"
                    f" {self.job_id}/{self.task_id} get unknown status: {task_status}"
                )
        log_info(
            "[train_action] training job has ended:"
            f" {self.job_id}/{self.task_id} with status: {task_status}"
        )
        return output

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        """
        resume method for train action

        Parameters:
            **kwargs (Dict):
                input args for action resume

        """
        if self.result is not None:
            log_warn("[train_action] already done")
            return self.result
        self.action_event(ActionState.Running, "train resume")
        if self.task_id is not None and self.job_id is not None:
            log_info(
                f"[train_action] resume from created job {self.task_id}/{self.job_id}"
            )
            train_metrics = self._wait_model_trained(**kwargs)
            self.result = {
                "task_id": self.task_id,
                "job_id": self.job_id,
                **train_metrics,
            }
            return self.result
        else:
            if self._input is None:
                self._input = {}
            return self._exec(self._input, **kwargs)

    def stop(self, **kwargs: Dict) -> "BaseAction":
        """
        stop method for train action

        Parameters:
            **kwargs (Dict):
                input args for action stop
        """
        if self.task_id is None or self.job_id is None:
            log_warn("[train_action] task_id or job_id not set, training not started")
            return self
        resp = api.FineTune.V2.stop_task(self.task_id)
        if resp.get("result"):
            log_debug(f"train task {self.task_id}/{self.job_id} stopped successfully")
        else:
            log_debug(f"train task {self.task_id}/{self.job_id} stopped failed")
        return self

    def get_default_train_config(
        self,
        model_type: str,
        train_mode: console_consts.TrainMode,
        peft_type: Optional[PeftType] = None,
    ) -> TrainConfig:
        model_info = get_default_train_config(train_mode).get(
            model_type,
        )
        if model_info is None or len(model_info) == 0:
            raise InvalidArgumentError(f"can not find default config for {model_type}")
        if peft_type is None:
            peft_type = sorted(model_info.keys())[0]
        train_config = model_info[peft_type]
        train_config.peft_type = peft_type
        return train_config

    def persist(self) -> bytes:
        return self.serialize_helper.serialize(self._action_dict())

    def _action_dict(self) -> Dict[str, Any]:
        meta = {
            "id": self.id,
            "type": TrainAction.__name__,
            "init_params": {
                "job_id": self._init_job_id,
                "task_id": self._init_task_id,
                "train_mode": (
                    self.train_mode
                    if isinstance(self.train_mode, str)
                    else self.train_mode.value
                ),
                "train_type": self.train_type,
                "train_config": (
                    self.train_config.dict() if self.train_config is not None else {}
                ),
                "is_incr": self.is_incr,
                "job_name": self.job_name,
                "task_description": self.task_description,
                "job_description": self.job_description,
            },
            "job_id": self.job_id if hasattr(self, "job_id") else None,
            "task_id": self.task_id if hasattr(self, "task_id") else None,
            "status": self.task_status,
            "progress": self.progress,
            "vdl_link": self.vdl_link,
            "log_link": self.log_link,
            "input": self._input,
            "output": self.result,
        }
        return meta

    @classmethod
    def _load_from_dict(cls, meta: Dict[str, Any]) -> "TrainAction":
        params = meta.get("init_params", {})
        if "train_config" in params:
            params["train_config"] = TrainConfig(**params["train_config"])
        action = cls(
            id=meta.get("id"),
            **params,
        )
        action.job_id = meta.get("job_id")
        action.task_id = meta.get("task_id")
        action.is_incr = params.pop("is_incr", False)
        action._input = meta.get("input")
        action.result = meta.get("output")
        action.task_status = meta.get("status")
        action.progress = meta.get("progress")
        action.vdl_link = meta.get("vdl_link")
        action.log_link = meta.get("log_link")
        return action


class ModelPublishAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """
    Class for Model publish action, Commonly used after `TrainAction`.

    Sample:

    Input:
    ```
    {'task_id': "task-xxx", 'job_id': "job-xxx"}
    ```

    Output:
    ```
    {'task_id': "task-xxx", 'job_id': "job-xxx", 'model_id': "xxx",
    'model_version_id': "aaa", "model": <Model>}
    ```
    """

    task_id: Optional[str] = None
    """task id"""
    job_id: Optional[str] = None
    """job id"""
    result: Optional[Dict[str, Any]] = None
    """result of model publish action"""
    model: Optional[Model] = None
    """model object"""

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        if self.task_id == "" or self.job_id == "":
            raise InvalidArgumentError("task_id or job_id must be set")
        self.task_id = input.get("task_id", "")
        self.job_id = input.get("job_id", "")
        self.model = Model(task_id=self.task_id, job_id=self.job_id)
        return self._exec(input, **kwargs)

    def _exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        self._input = input
        if self.model is None:
            raise InvalidArgumentError("model must be set when in model publish._exec")
        log_debug(
            f"[model_publish_action] start model publish task:, {self.task_id},"
            f" {self.job_id}"
        )
        try:
            self.action_event(
                ActionState.Running,
                "model publish",
                {
                    "task_id": self.task_id,
                    "job_id": self.job_id,
                },
            )
            self.model.publish(name=input.get("name", ""), **kwargs)
            log_debug(
                f"[model publish] model: {self.task_id}_{self.job_id} has been"
                " published."
            )

            self.result = {
                **input,
                "task_id": self.task_id,
                "job_id": self.job_id,
                "model_set_id": self.model.set_id,
                "model_id": self.model.id,
                "model": self.model,
            }
            return self.result
        except Exception as e:
            log_error(f"[model_publish_action] model publish error: {e}")
            raise e

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        # raise NotImplementedError("ModelPublishAction.resume() is not implemented")
        if self.result is not None:
            return self.result
        if self.model is not None:
            return self._exec()
        if self.task_id is None or self.job_id is None:
            raise InvalidArgumentError("task_id or job_id not set, resume failed")
        self.model = Model(task_id=self.task_id, job_id=self.job_id)
        return self._exec(**kwargs)

    def _action_dict(self) -> Dict[str, Any]:
        meta: Dict[str, Any] = {
            "id": self.id,
            "type": ModelPublishAction.__name__,
            "input": {
                "task_id": self.task_id,
                "job_id": self.job_id,
            },
        }
        if self.model:
            meta["model_id"] = self.model.id
        if self.result:
            res = copy.deepcopy(self.result)
            if "model" in res:
                res.pop("model")
            meta["output"] = res

        return meta

    @classmethod
    def _load_from_dict(cls, meta: Dict[str, Any]) -> "BaseAction":
        params = meta.get("init_params", {})
        action = cls(
            id=meta.get("id"),
            **params,
        )
        action._input = meta.get("input")  # type: ignore
        action.result = meta.get("output")
        action.model = Model(id=meta.get("model_id") or meta.get("model_version_id"))
        action.model.auto_complete_info()
        return action


class DeployAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """DeployAction
    Action for model service deployment. A TrainConfig must be supplied
    when instance initialized.
    Sample:
        ```
        deploy_config = DeployConfig(replicas=1, pool_type=1)
        deploy_action = DeployAction(deploy_config=deploy_config)

        output = deploy_action.exec(input)
        ```

    input:
        {'task_id': "task-xxxx", 'job_id': "job-xxxx", 'model_id': "xx",
        'model_version_id': "xxx"}
    output:
        ```
        {'task_id': "task-xxx", 'job_id': "job-xxxx", 'model_id': "xx",
        'model_version_id': "xxx",
        'service_id': 164, 'service_endpoint': 'xbiimimv_xxx'}
        ```
    """

    deploy_config: Optional[DeployConfig] = None
    """deploy config include replicas and so on"""
    """model id"""
    model_set_id: Optional[str] = None
    """model set id"""
    model_id: Optional[str] = None
    """model id """
    _input: Optional[Dict[str, Any]] = None
    """input of action"""
    result: Optional[Dict[str, Any]] = None
    """result of action"""
    model: Optional[Model] = None

    def __init__(self, deploy_config: Optional[DeployConfig] = None, **kwargs: Any):
        """

        Parameters:
            deploy_config (Optional[DeployConfig], optional):
                deploy config include replicas and so on. Defaults to None.
        """
        super().__init__(**kwargs)
        self.deploy_config = deploy_config

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Any) -> Dict[str, Any]:
        # for resume
        if self._input is None:
            self._input = input
        if self.deploy_config is None:
            raise InvalidArgumentError("deploy_config must be set")
        if input.get("model") is None:
            self.model_id = input.get("model_id")
            self.model_set_id = input.get("model_set_id")
            # TODO 迁移成str id
            if self.model_id is None or self.model_set_id is None:
                raise InvalidArgumentError("model_id or model_set_id must be set")

            self.model = Model(self.model_set_id, self.model_id, auto_complete=True)
            self.model.auto_complete_info()
        else:
            self.model = cast(Model, input.get("model"))
            if self.model is None:
                raise InvalidArgumentError(
                    "must input with model or model id and version id"
                )
            self.model.auto_complete_info()
        # 自动补全

        return self._exec(**kwargs)

    def _exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        if self.deploy_config is None:
            raise InvalidArgumentError("deploy_config must be set in deploy._exec")
        assert self.model is not None
        log_debug(
            f"[deploy_action] try deploy model {self.model.set_id}_{self.model.id}"
        )
        self.action_event(
            ActionState.Running,
            "ready to deploy",
            {
                "model": self.model,
            },
        )
        # deploy model
        self.model.deploy(self.deploy_config, **kwargs)
        if self.model.service is not None:
            log_debug(
                "[deploy_action] model"
                f" {self.model_set_id}_{self.model_id} deployed successfully with"
                " service:"
                f" {self.model.service.id} endpoint:{self.model.service.endpoint}"
            )
            return {
                **input,
                "service_id": self.model.service.id,
                "service_endpoint": self.model.service.endpoint,
                "service": self.model.service,
                "model": self.model,
            }
        else:
            raise InternalError("model.service is not available")

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        """
        resume method for deploy action

        Parameters:
            **kwargs (Dict):
                input args for action resume

        """
        if self.model_id is not None and self.model_set_id is not None:
            self.model = Model(self.model_set_id, self.model_id)
            self.model.auto_complete_info()
        elif self.model is None:
            raise InvalidArgumentError("either (set_id and id) or model must be set")
        return self._exec()

    def _action_dict(self) -> Dict[str, Any]:
        meta = {
            "id": self.id,
            "type": DeployAction.__name__,
            "init_params": {
                "deploy_config": (
                    self.deploy_config.dict() if self.deploy_config else None
                ),
            },
            "input": {
                "model_set_id": self.model_set_id,
                "model_id": self.model_id,
            },
        }
        if self.model is not None and self.model.service is not None:
            meta["output"] = {
                "service_id": self.model.service.id,
                "service_endpoint": self.model.service.endpoint,
            }
        return meta

    @classmethod
    def _load_from_dict(cls, meta: Dict[str, Any]) -> "BaseAction":
        deploy_config = meta.get("init_params", {}).get("deploy_config", {})
        action = cls(
            id=meta.get("id"),
            deploy_config=DeployConfig(**deploy_config),
        )
        action._input = meta.get("input")
        action.result = meta.get("output")
        return action


class BatchInferAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """BatchInferAction
    Action for batch inference.
    Sample:
    input:
        ```
        {'model_id': "am-xxxx", 'model_version_id': "amv-xxxx"}
        ```
    output:
        ```
        {'infer_res': InferenceResult ...}
        ```
    """

    # batch_inference_manager: Optional[BatchInferenceManager] = None
    """batch inference manager for batch infer models or services."""
    dataset: Optional[Dataset] = None


class EvaluateAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """EvaluateAction
    Action for evaluate models or services.
    Sample:
    input:
        ```
        {'model_id': "am-xxxx", 'model_version_id': "amv-xxxx"}
        ```
    output:
        ```
        {'eval_res': EvaluationResult ...}
        ```
    """

    eval_manager: Optional[EvaluationManager] = None
    """evaluation manager for evaluate models or services."""
    eval_dataset: Optional[Dataset] = None
    _input: Optional[Dict[str, Any]] = None
    """input of action"""
    result: Optional[Dict[str, Any]] = None
    """result of action"""

    def __init__(
        self, eval_dataset: Dataset, evaluators: List[Evaluator], **kwargs: Any
    ):
        """
        init method for evaluate action

        Parameters:
            eval_dataset Dataset:
                dataset for evaluation, use Dataset.load() to create.
            evaluators List[Evaluator]:
                evaluators for evaluation, include local and qianfan remote evaluators.
                Specifically, qianfan_evaluators are only available for Model.
        """
        super().__init__(**kwargs)
        self.eval_dataset = eval_dataset
        local_evaluators = [
            eval for eval in evaluators if isinstance(eval, LocalEvaluator)
        ]
        qianfan_evaluators = [
            eval for eval in evaluators if isinstance(eval, QianfanEvaluator)
        ]
        self.eval_manager = EvaluationManager(
            local_evaluators=local_evaluators if len(local_evaluators) > 0 else None,
            qianfan_evaluators=(
                qianfan_evaluators if len(qianfan_evaluators) > 0 else None
            ),
        )

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Any) -> Dict[str, Any]:
        """
        exec evaluation

        Parameters:
            input (Dict[str, Any], optional): input dict with model/service info.
            Defaults to {}.

        Returns:
            Dict[str, Any]: output the result with the original input
        """
        self._input = input
        log_info(f"[evaluation_action] begin to do evaluation, input: {self._input}")
        llm = self._parse_from_input(self._input)
        res = self._exec(llm, **kwargs)
        self.result = {"eval_res": res, **input}
        return self.result

    def _parse_from_input(self, input: Dict[str, Any] = {}) -> Union[Model, Service]:
        """
        Parses and returns the model or service object based on the input parameters.

        Parameters:
            input (Dict[str, Any], optional): . Defaults to {}.

        Returns:
            Union[Model, Service]: parsed model or service object
        """

        if input.get("service"):
            llm = input.get("service")
        elif input.get("model"):
            llm = input.get("model")
        elif input.get("model_set_id") and input.get("model_id"):
            llm = Model(input["model_set_id"], input["model_id"])
        else:
            log_error(f"[evaluation_action] invalid llm input error {self._input}")
            raise InvalidArgumentError(
                "model or service must be set in evaluation action"
            )
        assert isinstance(llm, (Model, Service))
        return llm

    def _exec(self, llm: Union[Model, Service], **kwargs: Any) -> Any:
        """
        accept a llm model/service to do evaluation

        Parameters:
            llm (Union[Model, Service]): model to do evaluation

        Returns:
            Any: evaluation result object
        """
        assert self.eval_manager is not None
        if self.eval_dataset is None:
            raise InvalidArgumentError("eval_dataset must be set")
        self.action_event(
            ActionState.Running,
            "ready to evaluate",
            {
                "llm": llm,
                "dataset": self.eval_dataset,
            },
        )
        log_info("[evaluation_action] running evaluation...")
        return self.eval_manager.eval([llm], self.eval_dataset, **kwargs)

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        """
        resume method for eval action

        Parameters:
            **kwargs (Dict):
                input args for action resume

        """
        if self._input is None:
            log_error(
                "[evaluation_action] previous input not found, call run() instead."
            )
            raise ValueError("input not found")
        llm = self._parse_from_input(self._input)
        res = self._exec(llm, **kwargs)
        self.result = {"eval_res": res, **self._input}
        return self.result

    def _action_dict(self) -> Dict[str, Any]:
        meta = {
            "id": self.id,
            "type": EvaluateAction.__name__,
            "init_params": {},
            # "input": self._input,
            # "output": self.result,
        }
        return meta

    @classmethod
    def _load_from_dict(cls, meta: Dict[str, Any]) -> "EvaluateAction":
        raise NotImplementedError()


action_mapping: Dict[str, Dict[str, Any]] = {
    LoadDataSetAction.__name__: {
        ActionState.Preceding: TrainStatus.DatasetLoading,
        ActionState.Running: TrainStatus.DatasetLoading,
        ActionState.Done: TrainStatus.DatasetLoaded,
        ActionState.Error: TrainStatus.DatasetLoadFailed,
        ActionState.Stopped: TrainStatus.DatasetLoadStopped,
    },
    TrainAction.__name__: {
        ActionState.Preceding: TrainStatus.TrainCreated,
        ActionState.Running: TrainStatus.Training,
        ActionState.Done: TrainStatus.TrainFinished,
        ActionState.Error: TrainStatus.TrainFailed,
        ActionState.Stopped: TrainStatus.TrainStopped,
    },
    ModelPublishAction.__name__: {
        ActionState.Preceding: TrainStatus.ModelPublishing,
        ActionState.Running: TrainStatus.ModelPublishing,
        ActionState.Done: TrainStatus.ModelPublished,
        ActionState.Error: TrainStatus.ModelPublishFailed,
        ActionState.Stopped: TrainStatus.ModelPublishFailed,
    },
    DeployAction.__name__: {
        ActionState.Preceding: ServiceStatus.Created,
        ActionState.Running: ServiceStatus.Deploying,
        ActionState.Done: ServiceStatus.Deployed,
        ActionState.Error: ServiceStatus.DeployFailed,
        ActionState.Stopped: ServiceStatus.DeployStopped,
    },
    EvaluateAction.__name__: {
        ActionState.Preceding: TrainStatus.EvaluationCreated,
        ActionState.Running: TrainStatus.EvaluationRunning,
        ActionState.Done: TrainStatus.EvaluationFinished,
        ActionState.Error: TrainStatus.EvaluationFailed,
        ActionState.Stopped: TrainStatus.EvaluationStopped,
    },
}


log_prefix_mapping = {
    console_consts.TrainMode.SFT: "sft",
    console_consts.TrainMode.PostPretrain: "postPretrain",
    console_consts.TrainMode.DPO: "dpo",
}
