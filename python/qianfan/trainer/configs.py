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
import datetime
import hashlib
import threading
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

import cachetools

from qianfan.config import encoding
from qianfan.errors import InvalidArgumentError
from qianfan.resources import FineTune
from qianfan.resources.console import consts as console_consts
from qianfan.trainer.consts import PeftType
from qianfan.utils import log_error, log_warn
from qianfan.utils.pydantic import BaseModel, Field, create_model, validator
from qianfan.utils.utils import camel_to_snake

T = TypeVar("T")


LimitType = console_consts.FinetuneSupportHyperParameterCheckType


class DatasetConfig(BaseModel):
    datasets: List[Any]
    """
    datasets
    """
    sampling_rates: Optional[List[float]] = None
    """
    sampling_rates for each dataset
    """
    eval_split_ratio: Optional[float] = None
    """
    training evaluation split ratio
    """
    corpus_proportion: Optional[float] = None
    """
    corpus proportion, only support in `QianfanCommon` Corpus
    """
    corpus_type: Optional[console_consts.FinetuneCorpusType] = None
    """
    corpus type, including qianfan/yiyan common/yiyan vertical
    """
    corpus_labels: Optional[List[str]] = None
    """
    corpus vertical labels
    """
    sampling_rate: Optional[float] = None
    """
    sampling rate in global
    """
    source_type: Optional[Union[str, console_consts.TrainDatasetSourceType]] = None
    """
    source type, must be specified when dataset is dict type
    """


class BaseJsonModel(BaseModel):
    class Config:
        allow_population_by_field_name = True


class CorpusConfigItem(BaseJsonModel):
    corpus_proportion: Optional[Any] = Field(default=None, alias="proportion")
    """
    corpus proportion, only support in `QianfanCommon` Corpus
    """
    corpus_type: Optional[int] = Field(default=None, alias="corpusType")
    """
    corpus type, including qianfan/yiyan common/yiyan vertical
    """
    corpus_labels: Optional[List[str]] = Field(default=None, alias="labels")
    """
    corpus vertical labels
    """

    @validator("corpus_type", pre=True)
    def convert_enum_to_int(cls, v: Any) -> Any:
        if isinstance(v, console_consts.FinetuneCorpusType):
            return v.value
        return v


class CorpusConfig(BaseJsonModel):
    copy_data: Optional[bool] = Field(default=None, alias="copyData")
    """
    copy data when exceed maximum number of data
    """
    corpus_configs: List[CorpusConfigItem] = Field(default=[], alias="config")
    """
    corpus configs
    """


class ResourceConfig(BaseJsonModel):
    resource_id: str = Field(default=[], alias="resourceId")
    """
    resource ids
    """
    node_num: Optional[int] = Field(default=None, alias="nodeNum")
    """
    node num
    """


class BaseTrainConfig(BaseModel):
    peft_type: Optional[Union[str, PeftType]] = None
    """
    parameter efficient FineTuning method, like `LoRA`, `P-tuning`, `ALL`
    """
    trainset_rate: Optional[int] = None
    """
    rate for dataset to spilt, use DatasetConfig to configure the split ratio
    """
    extras: Dict[str, Any] = {}
    """
    extra fields for train_config
    """
    resource_config: Optional[ResourceConfig] = None

    def validate_config(self, train_limit: "TrainLimit") -> bool:
        schema = self.schema()
        res = True
        for k, v in schema["properties"].items():
            limit_type = v.get("limit_type")
            if limit_type is None:
                continue
            value = getattr(self, k)
            if value is None:
                continue
            if k not in train_limit:
                log_warn(
                    f"train_config hyper params '{k}' is not in supported_params:"
                    f" {train_limit}"
                )
                return False
            if limit_type == LimitType.Range:
                res &= self._validate_range(value, train_limit[k], k)
            elif limit_type == LimitType.Choice:
                res &= self._validate_options(value, train_limit[k], k)
            elif limit_type == LimitType.MultipleChoice:
                for v in value:
                    res &= self._validate_options(v, train_limit[k], k)
            if not res:
                break
        return res

    def _validate_range(
        self, value: Any, limit_ranges: Optional[List[T]], field_name: str
    ) -> bool:
        """
        return False if value is not in limit_ranges
        if limit_ranges is None, return True

        Args:
            value (Any): field value
            limit_ranges (List[Optional[Tuple[T, T]]]): field valid value range
            field_name (str): field name

        Returns:
            bool: result
        """
        if value is None or limit_ranges is None:
            return True
        if limit_ranges is None:
            return True
        if len(limit_ranges) == 1:
            limit_ranges = [limit_ranges[0], limit_ranges[0]]
        if limit_ranges[0] > value or limit_ranges[1] < value:
            log_warn(
                f"train_config current {field_name} is {value}:"
                f" but suggested {field_name} is in {limit_ranges}"
            )
            return False
        return True

    def _validate_options(
        self, value: Any, options: Optional[List[T]], field_name: str
    ) -> bool:
        """
        return False if value is not in options
        if options is None, return True

        Args:
            value (Any): field value
            options (List[Any]): field valid value option
            field_name (str): field name

        Returns:
            bool: result
        """
        if value is None or options is None:
            return True
        if value not in options:
            log_warn(
                f"train_config current {field_name} is {value}:"
                f" but suggested {field_name} is in {options}"
            )
            return False
        return True


class TrainConfigImpl(BaseTrainConfig):
    epoch: Optional[int] = Field(default=None, limit_type=LimitType.Range)
    """
    epoch number: differ from models
    """
    batch_size: Optional[int] = Field(default=None, limit_type=LimitType.Range)
    """
    batch size: differ from models
    """
    learning_rate: Optional[float] = Field(default=None, limit_type=LimitType.Range)
    """
    learning rate: differ from models
    """
    max_seq_len: Optional[int] = Field(default=None, limit_type=LimitType.Choice)
    """
    max_seq_len: differ from models
    """
    logging_steps: Optional[int] = Field(default=None, limit_type=LimitType.Range)
    """log saving interval steps"""
    warmup_ratio: Optional[float] = Field(default=None, limit_type=LimitType.Range)
    """warmup ratio"""
    weight_decay: Optional[float] = Field(default=None, limit_type=LimitType.Range)
    """normalization params"""
    lora_rank: Optional[int] = Field(default=None, limit_type=LimitType.Choice)
    """loRA rank"""
    lora_all_linear: Optional[str] = Field(default=None, limit_type=LimitType.Choice)
    """loRA all linear layer"""
    scheduler_name: Optional[str] = Field(default=None, limit_type=LimitType.Choice)
    """for learning rate schedule"""
    lora_alpha: Optional[int] = Field(default=None, limit_type=LimitType.Range)
    """LoRA scaling params"""
    lora_dropout: Optional[float] = Field(default=None, limit_type=LimitType.Range)
    """loRA dropout"""
    lora_target_modules: Optional[List[str]] = Field(
        default=None, limit_type=LimitType.MultipleChoice
    )
    """LoRA参数层列表"""


def _load_config(path: str) -> "TrainConfigImpl":
    import yaml

    try:
        from pathlib import Path

        path_obj = Path(path)
        if path_obj.suffix == ".yaml":
            with open(path_obj, "r", encoding=encoding()) as file:
                data = yaml.safe_load(file)
                return TrainConfigImpl.parse_obj(data)
        elif path_obj.suffix == ".json":
            return TrainConfigImpl.parse_file(path)
        else:
            raise InvalidArgumentError("unsupported file to parse: {path}")
    except FileNotFoundError as e:
        log_error(f"load train_config from file: {path} not found")
        raise e
    except Exception as e:
        raise e


class TrainConfig(object):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        need_update = kwargs.get("need_update", True)
        if need_update:
            update_all()
        if kwargs.get("real_train_config"):
            self.real_train_config = kwargs.get("real_train_config")
        else:
            self.real_train_config = TrainConfigImpl(*args, **kwargs)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in ["real_train_config", "load"]:
            return super().__setattr__(__name, __value)
        self.real_train_config.__setattr__(__name, __value)

    def __getattribute__(self, __name: str) -> Any:
        if __name == "real_train_config":
            return super().__getattribute__(__name)
        return self.real_train_config.__getattribute__(__name)

    def __str__(self) -> str:
        return self.real_train_config.__str__()

    @classmethod
    def load(cls, path: str) -> "TrainConfig":
        try:
            update_all()
            tc = TrainConfig(real_train_config=_load_config(path), need_update=False)

            return tc
        except Exception as e:
            log_error(e)
            raise e


class TrainLimit(dict):
    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)
            self.__setitem__(k, v)

    def __or__(self, other: Any) -> "TrainLimit":
        assert isinstance(other, TrainLimit)
        merged_data = copy.deepcopy(self)

        for field, value in other.items():
            if merged_data.get(field) is None:
                merged_data[field] = value

        # 创建一个新的BaseModel对象，使用合并后的数据
        merged_model = self.__class__(**merged_data)
        return merged_model


class ModelInfo(BaseModel):
    model: str = ""
    """
    model used to create train task
    """
    short_name: str
    """
    short_name must be shorter than 15 characters
    """
    base_model_type: str = ""
    """
    [deprecated] base model name
    """
    support_peft_types: List[PeftType] = []
    """support peft types and suggestions for training params"""
    common_params_limit: TrainLimit = TrainLimit()
    """common params limit, except suggestion params
    diverse from different peft types"""
    specific_peft_types_params_limit: Optional[
        Dict[Union[str, PeftType], TrainLimit]
    ] = None
    """special params suggestion of specific peft types"""
    model_type: console_consts.FinetuneSupportModelType = (
        console_consts.FinetuneSupportModelType.Text2Text
    )
    """
    model type, like text2text, image2image
    """
    deprecated: bool = False
    """
    if it's deprecated model
    """


def get_model_info(
    train_mode: console_consts.TrainMode, model: str
) -> Optional[ModelInfo]:
    return get_trainer_model_list(train_mode).get(model)


def _get_online_supported_model_info_mapping(
    model_info_list: List[Any], train_mode: console_consts.TrainMode
) -> Dict[str, ModelInfo]:
    try:
        # 更新校验限制 & 更新模型默认配置
        return _parse_model_info_list(
            model_info_list=model_info_list, train_mode=train_mode
        )
    except ValueError as e:
        log_warn(f"get latest model info failed, {e}")
    return {}


def create_train_config_class(class_name: str, fields: Dict[str, Any]) -> Type:
    annotations: Any = {}
    # 遍历字段字典，将字段名称和类型添加到字典中
    for field_name, field_info in fields.items():
        annotations[field_name] = (
            Optional[field_info.get("type", str)],
            Field(**field_info),
        )  # 将字段类型修改为 Optional
    # 使用 create_model 函数创建一个动态生成的类
    dynamic_class = create_model(  # type: ignore
        __model_name=class_name,
        __base__=BaseTrainConfig,
        **annotations,
    )
    return dynamic_class


type_mapping = {
    "integer": int,
    "string": str,
    "number": float,
    "array": list,
    "float": float,
    "int": int,
    "str": str,
    "boolean": bool,
    "bool": bool,
}


def _update_train_config(model_info_list: List[Dict]) -> Type:
    # 使用动态生成类的函数创建 TrainConfig 类
    global TrainConfigImpl
    schema_dict = TrainConfigImpl.schema()
    # try:
    train_config_fields = {}
    params = schema_dict.get("properties", {})
    for key, val in params.items():
        if val.get("type", None):
            if "limit_type" not in val:
                continue
            field_info: Dict[str, Any] = {}
            if val["type"] in type_mapping:
                field_info["type"] = type_mapping[val["type"]]
                field_info["limit_type"] = val["limit_type"]
                field_info["default"] = None

                train_config_fields[key] = field_info

    for info in model_info_list:
        for train_mode_info in info["supportTrainMode"]:
            for param_scale in train_mode_info["supportParameterScale"]:
                for params in param_scale["supportHyperParameterConfig"]:
                    try:
                        field_name = camel_to_snake(params["key"])
                        train_config_fields[field_name] = {
                            "type": type_mapping[params["type"]],
                            "limit_type": LimitType(params["checkType"]),
                            "default": None,
                            "origin_key": params["key"],
                        }
                        if params["checkType"] == "mult_choice":
                            train_config_fields[field_name]["type"] = list
                    except Exception as e:
                        log_warn(f'invalid field name: {params["key"]} err: {e}')
                        continue

    new_train_config_type = create_train_config_class(
        "TrainConfigImpl", train_config_fields
    )
    # except Exception as e:
    #     log_error(f"update train config failed, {e}")
    #     return TrainConfig

    TrainConfigImpl = new_train_config_type  # type: ignore
    return TrainConfigImpl


def _update_default_config(model_info_list: List[Dict]) -> Dict:
    train_mode_model_info_mappings: Dict[str, Any] = {
        console_consts.TrainMode.PostPretrain: {},
        console_consts.TrainMode.SFT: {},
        console_consts.TrainMode.DPO: {},
    }
    for info in model_info_list:
        model = info["model"]
        for train_mode_info in info["supportTrainMode"]:
            train_mode = train_mode_info.get("trainMode")
            current = train_mode_model_info_mappings.get(train_mode, {})
            if not current.get(model, None):
                current[model] = {}
            for param_scale in train_mode_info["supportParameterScale"]:
                default_fields = {}
                param_scale_peft = param_scale["parameterScale"]
                for params in param_scale["supportHyperParameterConfig"]:
                    field_name = camel_to_snake(params["key"])
                    default_fields[field_name] = params["default"]
                current[model][param_scale_peft] = TrainConfig(
                    **default_fields, need_update=False
                )
    return train_mode_model_info_mappings


def _parse_model_info_list(
    model_info_list: List[Dict], train_mode: console_consts.TrainMode
) -> Dict[str, ModelInfo]:
    """
    parse the supported fine-tune info list, update the train_limit

    Args:
        model_info_list: the list of model info

    Return:
        model_info_mapping: (Dict[Dict[str, ModelInfo]])
    """
    model_info_mapping = {}
    for info in model_info_list:
        model = info["model"]
        model_hash = hashlib.sha256(model.encode()).hexdigest()[:8]
        m = ModelInfo(
            model=model,
            short_name=f"model{model_hash}",
            base_model_type=info.get("baseModel", ""),
            support_peft_types=[],
            specific_peft_types_params_limit={},
            model_type=console_consts.FinetuneSupportModelType(
                info.get("modelType", console_consts.FinetuneSupportModelType.Text2Text)
            ),
        )
        has_train_mode = False
        for train_mode_info in info["supportTrainMode"]:
            if train_mode.value != train_mode_info.get("trainMode"):
                continue
            has_train_mode = True
            for param_scale in train_mode_info["supportParameterScale"]:
                train_limit = TrainLimit()
                param_scale_peft = param_scale["parameterScale"]
                if param_scale_peft not in m.support_peft_types:
                    m.support_peft_types.append(PeftType(param_scale_peft))
                for params in param_scale["supportHyperParameterConfig"]:
                    field_name = camel_to_snake(params["key"])
                    train_limit[field_name] = params["checkValue"]
                m.specific_peft_types_params_limit[param_scale_peft] = train_limit  # type: ignore
        if has_train_mode:
            model_info_mapping[model] = m
    return model_info_mapping


PostPreTrainModelInfoMapping: Dict[str, ModelInfo] = {
    "ERNIE-Speed": ModelInfo(
        model="ERNIE-Speed-8K",
        short_name="ERNIE_Speed",
        base_model_type="ERNIE Speed",
        deprecated=True,
    ),
    "Qianfan-Chinese-Llama-2-13B": ModelInfo(
        model="Qianfan-Chinese-Llama-2-13B-v2",
        base_model_type="Llama",
        short_name="Llama2_13b",
    ),
    "Qianfan-Chinese-Llama-2-13B-v2": ModelInfo(
        model="Qianfan-Chinese-Llama-2-13B-v2",
        base_model_type="Llama",
        short_name="Llama2_13b",
    ),
}


DPOTrainModelInfoMapping: Dict[str, ModelInfo] = {}

# model train type -> default train config, dynamic fetch from api
ModelInfoMapping: Dict[str, ModelInfo] = {
    "ERNIE-Speed": ModelInfo(
        model="ERNIE-Speed-8K",
        short_name="ERNIE_Speed",
        base_model_type="ERNIE Speed",
        deprecated=True,
    ),
    "Qianfan-Chinese-Llama-2-13B": ModelInfo(
        model="Qianfan-Chinese-Llama-2-13B-v2",
        short_name="Llama2_13b",
        base_model_type="Llama",
    ),
    "Qianfan-Chinese-Llama-2-13B-v2": ModelInfo(
        model="Qianfan-Chinese-Llama-2-13B-v2",
        short_name="Llama2_13b",
        base_model_type="Llama",
    ),
}

DefaultPostPretrainTrainConfigMapping: Dict[str, Dict[PeftType, TrainConfig]] = {}

DefaultDPOTrainConfigMapping: Dict[str, Dict[PeftType, TrainConfig]] = {}

# finetune model train type -> default finetune train config
DefaultTrainConfigMapping: Dict[str, Dict[PeftType, TrainConfig]] = {}


ttl_cache: cachetools.Cache = cachetools.TTLCache(maxsize=200, ttl=7200)


ModelInfoMappingCollection: Dict[str, Dict[str, ModelInfo]] = {}
DefaultTrainConfigMappingCollection: Dict[
    str, Dict[str, Dict[PeftType, TrainConfig]]
] = {}


def get_trainer_model_list(
    train_mode: Union[str, console_consts.TrainMode]
) -> Dict[str, ModelInfo]:
    update_all()
    return ModelInfoMappingCollection.get(
        console_consts.TrainMode(train_mode).value, {}
    )


def get_default_train_config(
    train_mode: Union[str, console_consts.TrainMode]
) -> Dict[str, Dict[PeftType, TrainConfig]]:
    update_all()
    train_configs = DefaultTrainConfigMappingCollection.get(
        console_consts.TrainMode(train_mode).value, {}
    )
    return train_configs


@cachetools.cached(ttl_cache)
def get_supported_models() -> Any:
    return FineTune.V2.supported_models()["result"]


last_update_time: Optional[datetime.datetime] = None
lock = threading.Lock()


def interval_call_checker(c: Callable, interval: int = 3000) -> Callable:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        need_call = False
        with lock:
            global last_update_time
            if last_update_time is None:
                last_update_time = datetime.datetime.now()
                need_call = True
            else:
                now = datetime.datetime.now()
                if (now - last_update_time).seconds > interval:
                    last_update_time = now
                    need_call = True
        if need_call:
            return c(*args, **kwargs)
        else:
            return None

    return wrapper


@interval_call_checker
def update_all(*args: Any, **kwargs: Any) -> None:
    update_train_configs()
    update_model_list_configs()


def update_train_configs() -> "Type":
    try:
        # 获取最新支持的配置：
        model_info_list = get_supported_models()
        # 更新训练config
        return _update_train_config(model_info_list=model_info_list)
    except Exception as e:
        log_warn(f"failed to get supported models: {e}")
        return TrainConfig


def update_model_list_configs() -> None:
    try:
        # 获取最新支持的配置：
        model_info_list = get_supported_models()
        # 更新模型列表的类型和校验参数
        sft_model_info = _get_online_supported_model_info_mapping(
            model_info_list, console_consts.TrainMode.SFT
        )
        ppt_model_info = _get_online_supported_model_info_mapping(
            model_info_list, console_consts.TrainMode.PostPretrain
        )
        dpo_model_info = _get_online_supported_model_info_mapping(
            model_info_list, console_consts.TrainMode.DPO
        )
        # 更新模型默认配置：
        default_configs_mapping = _update_default_config(model_info_list)
    except Exception as e:
        raise e
        return
    # 更新
    global ModelInfoMappingCollection, ModelInfoMapping
    global PostPreTrainModelInfoMapping, DPOTrainModelInfoMapping
    ModelInfoMapping = {**ModelInfoMapping, **sft_model_info}
    PostPreTrainModelInfoMapping = {
        **PostPreTrainModelInfoMapping,
        **ppt_model_info,
    }
    DPOTrainModelInfoMapping = {**DPOTrainModelInfoMapping, **dpo_model_info}
    ModelInfoMappingCollection[console_consts.TrainMode.SFT.value] = ModelInfoMapping
    ModelInfoMappingCollection[console_consts.TrainMode.PostPretrain.value] = (
        PostPreTrainModelInfoMapping
    )
    ModelInfoMappingCollection[console_consts.TrainMode.DPO.value] = (
        DPOTrainModelInfoMapping
    )

    def fix_deprecated_model_infos(model_mapping: Dict[str, ModelInfo]) -> None:
        for model, model_info in model_mapping.items():
            if (
                len(model_info.support_peft_types) == 0
                and model_info.model in model_mapping
            ):
                model_mapping[model] = model_mapping[model_info.model]

    def fix_deprecated_model_train_configs(
        train_configs: Dict[str, Dict[PeftType, TrainConfig]]
    ) -> None:
        model_list = get_trainer_model_list(train_mode)
        for model, model_info in model_list.items():
            if model not in train_configs and model_info.model in train_configs:
                train_configs[model] = train_configs[model_info.model]

    # default train configs
    global DefaultTrainConfigMappingCollection, DefaultTrainConfigMapping
    global DefaultPostPretrainTrainConfigMapping, DefaultDPOTrainConfigMapping
    DefaultTrainConfigMapping = {
        **DefaultTrainConfigMapping,
        **default_configs_mapping[console_consts.TrainMode.SFT],
    }
    DefaultPostPretrainTrainConfigMapping = {
        **DefaultPostPretrainTrainConfigMapping,
        **default_configs_mapping[console_consts.TrainMode.PostPretrain],
    }
    DefaultDPOTrainConfigMapping = {
        **DefaultDPOTrainConfigMapping,
        **default_configs_mapping[console_consts.TrainMode.DPO],
    }
    DefaultTrainConfigMappingCollection[console_consts.TrainMode.SFT.value] = (
        DefaultTrainConfigMapping
    )
    DefaultTrainConfigMappingCollection[console_consts.TrainMode.PostPretrain.value] = (
        DefaultPostPretrainTrainConfigMapping
    )
    DefaultTrainConfigMappingCollection[console_consts.TrainMode.DPO.value] = (
        DefaultDPOTrainConfigMapping
    )

    for train_mode in console_consts.TrainMode:
        model_mapping = ModelInfoMappingCollection.get(train_mode.value, {})
        fix_deprecated_model_infos(model_mapping)

        train_configs = DefaultTrainConfigMappingCollection.get(train_mode.value, {})
        fix_deprecated_model_train_configs(train_configs)
    return None
