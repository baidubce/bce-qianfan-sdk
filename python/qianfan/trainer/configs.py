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
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from qianfan.config import encoding
from qianfan.errors import InvalidArgumentError
from qianfan.resources.console import consts as console_consts
from qianfan.trainer.consts import PeftType
from qianfan.utils import log_error, log_warn
from qianfan.utils.pydantic import BaseModel, Field

T = TypeVar("T")


class LimitType(int, Enum):
    SingleChoice = 1
    MultipleChoice = 2
    Range = 3


class TrainConfig(BaseModel):
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
    max_seq_len: Optional[int] = Field(default=None, limit_type=LimitType.SingleChoice)
    """
    max_seq_len: differ from models
    """
    logging_steps: Optional[int] = Field(default=None, limit_type=LimitType.Range)
    """log saving interval steps"""
    warmup_ratio: Optional[float] = Field(default=None, limit_type=LimitType.Range)
    """warmup ratio"""
    weight_decay: Optional[float] = Field(default=None, limit_type=LimitType.Range)
    """normalization params"""
    lora_rank: Optional[int] = Field(default=None, limit_type=LimitType.SingleChoice)
    """loRA rank"""
    lora_all_linear: Optional[str] = Field(
        default=None, limit_type=LimitType.SingleChoice
    )
    """loRA all linear layer"""
    scheduler_name: Optional[str] = Field(
        default=None, limit_type=LimitType.SingleChoice
    )
    """for learning rate schedule"""
    lora_alpha: Optional[int] = Field(default=None, limit_type=LimitType.Range)
    """LoRA scaling params"""
    lora_dropout: Optional[float] = Field(default=None, limit_type=LimitType.Range)
    """loRA dropout"""
    lora_target_modules: Optional[List[str]] = Field(
        default=None, limit_type=LimitType.MultipleChoice
    )
    """LoRA参数层列表"""

    peft_type: Optional[Union[str, PeftType]] = None
    """
    parameter efficient FineTuning method, like `LoRA`, `P-tuning`, `ALL`
    """
    trainset_rate: int = 20
    """
    rate for dataset to spilt 
    """
    extras: Dict[str, Any] = {}
    """
    extra fields for train_config
    """

    @classmethod
    def load(cls, path: str) -> "TrainConfig":
        import yaml

        try:
            from pathlib import Path

            path_obj = Path(path)
            if path_obj.suffix == ".yaml":
                with open(path_obj, "r", encoding=encoding()) as file:
                    data = yaml.safe_load(file)
                    return TrainConfig.parse_obj(data)
            elif path_obj.suffix == ".json":
                return cls.parse_file(path)
            else:
                raise InvalidArgumentError("unsupported file to parse: {path}")
        except FileNotFoundError as e:
            log_error(f"load train_config from file: {path} not found")
            raise e
        except Exception as e:
            raise e

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
            elif limit_type == LimitType.SingleChoice:
                res &= self._validate_options(value, train_limit[k], k)
            elif limit_type == LimitType.MultipleChoice:
                for v in value:
                    res &= self._validate_options(v, train_limit[k], k)
            if not res:
                break
        return res

    def _validate_range(
        self, value: Any, limit_ranges: Optional[Tuple[T, T]], field_name: str
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


class TrainLimit(dict):
    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)
            self.__setitem__(k, v)

    def __or__(self, other: Any) -> "TrainLimit":
        assert isinstance(other, TrainLimit)
        # 使用copy模块深拷贝a的数据，避免修改原始数据
        merged_data = copy.deepcopy(self)

        # 遍历b的字段，如果a中的值为None，则取b的值
        for field, value in other.items():
            if merged_data.get(field) is None:
                merged_data[field] = value

        # 创建一个新的BaseModel对象，使用合并后的数据
        merged_model = self.__class__(**merged_data)
        return merged_model


class ModelInfo(BaseModel):
    short_name: str
    """
    short_name must be shorter than 15 characters
    """
    base_model_type: str
    """
    base model name
    """
    support_peft_types: List[PeftType] = []
    """support peft types and suggestions for training params"""
    common_params_limit: TrainLimit
    """common params limit, except suggestion params
    diverse from different peft types"""
    specific_peft_types_params_limit: Optional[
        Dict[Union[str, PeftType], TrainLimit]
    ] = None
    """special params suggestion of specific peft types"""


def get_model_info(
    train_mode: console_consts.TrainMode, model: str
) -> Optional[ModelInfo]:
    if train_mode == console_consts.TrainMode.PostPretrain:
        return PostPreTrainModelInfoMapping.get(model)
    elif train_mode == console_consts.TrainMode.SFT:
        return ModelInfoMapping.get(model)
    else:
        return None


PostPreTrainModelInfoMapping: Dict[str, ModelInfo] = {
    "ERNIE-Speed": ModelInfo(
        short_name="ERNIE_Speed",
        base_model_type="ERNIE-Speed",
        support_peft_types=[PeftType.ALL],
        common_params_limit=TrainLimit(),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                epoch=(1, 10),
                learning_rate=(0.00001, 0.00004),
                max_seq_len=[4096, 8192],
            ),
        },
    ),
    "ERNIE-Bot-turbo-0922": ModelInfo(
        short_name="turbo_0922",
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL],
        common_params_limit=TrainLimit(),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                epoch=(1, 10),
                learning_rate=(0.00001, 0.00004),
                max_seq_len=[4096, 8192],
            ),
        },
    ),
    "Qianfan-Chinese-Llama-2-13B": ModelInfo(
        short_name="Llama2_13b",
        base_model_type="Llama-2",
        support_peft_types=[PeftType.ALL],
        common_params_limit=TrainLimit(),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                batch_size=(48, 960),
                epoch=(1, 1),
                learning_rate=(0.0000002, 0.0002),
                weight_decay=(0.0001, 0.05),
            ),
        },
    ),
}

# model train type -> default train config
ModelInfoMapping: Dict[str, ModelInfo] = {
    "ERNIE-Speed": ModelInfo(
        short_name="ERNIE_Speed",
        base_model_type="ERNIE-Speed",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            max_seq_len=[4096, 8192],
            epoch=(1, 50),
            logging_steps=(1, 100),
            warmup_ratio=(0.01, 0.5),
            weight_decay=(0.0001, 0.1),
        ),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                learning_rate=(0.00001, 0.00004),
            ),
            PeftType.LoRA: TrainLimit(
                learning_rate=(0.00003, 0.001),
                lora_rank=[2, 4, 8],
                lora_all_linear=["True", "False"],
            ),
        },
    ),
    "ERNIE-Bot-turbo-0922": ModelInfo(
        short_name="turbo_0922",
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            max_seq_len=[4096, 8192],
            epoch=(1, 50),
            logging_steps=(1, 100),
            warmup_ratio=(0.01, 0.5),
            weight_decay=(0.0001, 0.1),
        ),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                learning_rate=(0.00001, 0.00004),
            ),
            PeftType.LoRA: TrainLimit(
                learning_rate=(0.00003, 0.001),
                lora_rank=[2, 4, 8],
            ),
        },
    ),
    "ERNIE-Bot-turbo-0725": ModelInfo(
        short_name="turbo_0725",
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            max_seq_len=[4096, 8192],
            epoch=(1, 50),
        ),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                learning_rate=(0.00001, 0.00004),
            ),
            PeftType.LoRA: TrainLimit(
                learning_rate=(0.00003, 0.001),
            ),
        },
    ),
    "ERNIE-Bot-turbo-0704": ModelInfo(
        short_name="turbo_0704",
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            epoch=(1, 50),
        ),
        specific_peft_types_params_limit={
            PeftType.PTuning: TrainLimit(
                learning_rate=(0.003, 0.1),
            ),
            PeftType.ALL: TrainLimit(
                learning_rate=(0.00001, 0.00004),
            ),
            PeftType.LoRA: TrainLimit(
                learning_rate=(0.00003, 0.001),
            ),
        },
    ),
    "Qianfan-Chinese-Llama-2-7B": ModelInfo(
        short_name="Llama2_7b",
        base_model_type="Llama-2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            max_seq_len=[1024, 2048, 4096],
            epoch=(1, 50),
            learning_rate=(0.0000002, 0.0002),
            scheduler_name=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
            weight_decay=(0.001, 1),
            warmup_ratio=(0.01, 0.1),
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank=[8, 16, 32, 64],
                lora_alpha=[8, 16, 32, 64],
                lora_dropout=(0.1, 0.5),
            ),
        },
    ),
    "Qianfan-Chinese-Llama-2-13B": ModelInfo(
        short_name="Llama2_13b",
        base_model_type="Llama-2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            max_seq_len=[1024, 2048, 4096],
            epoch=(1, 50),
            learning_rate=(0.0000002, 0.0002),
            scheduler_name=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
            weight_decay=(0.001, 1),
            warmup_ratio=(0.01, 0.1),
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank=[8, 16, 32, 64],
                lora_alpha=[8, 16, 32, 64],
                lora_dropout=(0.1, 0.5),
            ),
        },
    ),
    "Qianfan-Chinese-Llama-2-7B-32K": ModelInfo(
        short_name="Llama2_13b_32K",
        base_model_type="Llama-2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size=(1, 1),
            max_seq_len=[4096, 8192, 16384, 32768],
            epoch=(1, 50),
            learning_rate=(0.0000000001, 0.0002),
            scheduler_name=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
            weight_decay=(0.001, 1),
            warmup_ratio=(0.01, 0.1),
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank=[8, 16, 32, 64],
                lora_alpha=[8, 16, 32, 64],
                lora_dropout=(0.1, 0.5),
            ),
        },
    ),
    "SQLCoder-7B": ModelInfo(
        short_name="SQLCoder_7B",
        base_model_type="SQLCoder",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            max_seq_len=[4096, 8192],
            epoch=(1, 50),
            learning_rate=(0.0000002, 0.0002),
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank=[8, 16, 32, 64],
                lora_alpha=[8, 16, 32, 64],
                lora_dropout=(0.1, 0.5),
            ),
        },
    ),
    "ChatGLM2-6B": ModelInfo(
        short_name="GLM2_6B",
        base_model_type="ChatGLM2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            epoch=(1, 50),
            batch_size=(1, 4),
            max_seq_len=[1024, 2048, 4096],
            scheduler_name=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
            learning_rate=(0.0000002, 0.0002),
            warmup_ratio=(0.01, 0.1),
            weight_decay=(0.001, 1),
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank=[8, 16, 32, 64],
                lora_alpha=[8, 16, 32, 64],
                lora_dropout=(0.1, 0.5),
            ),
        },
    ),
    "ChatGLM2-6B-32K": ModelInfo(
        short_name="GLM2_6B_32K",
        base_model_type="ChatGLM2",
        support_peft_types=[PeftType.ALL],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            max_seq_len=[1024, 2048, 4096],
            epoch=(1, 50),
            learning_rate=(0.0000002, 0.0002),
            warmup_ratio=(0.01, 0.1),
            weight_decay=(0.001, 1),
            scheduler_name=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
        ),
    ),
    "Baichuan2-7B-Chat": ModelInfo(
        short_name="Baichuan2_7B",
        base_model_type="Baichuan2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            max_seq_len=[1024, 2048, 4096],
            epoch=(1, 50),
            learning_rate=(0.0000000001, 0.0002),
            warmup_ratio=(0.01, 0.1),
            weight_decay=(0.001, 1),
            scheduler_name=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank=[8, 16, 32, 64],
                lora_alpha=[8, 16, 32, 64],
                lora_dropout=(0.1, 0.5),
            )
        },
    ),
    "Baichuan2-13B-Chat": ModelInfo(
        short_name="Baichuan2_13B",
        base_model_type="Baichuan2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            max_seq_len=[1024, 2048, 4096],
            epoch=(1, 50),
            learning_rate=(0.0000000001, 0.0002),
            warmup_ratio=(0.01, 0.1),
            weight_decay=(0.001, 1),
            scheduler_name=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank=[8, 16, 32, 64],
                lora_alpha=[8, 16, 32, 64],
                lora_dropout=(0.1, 0.5),
            )
        },
    ),
    "BLOOMZ-7B": ModelInfo(
        short_name="BLOOMZ_7B",
        base_model_type="BLOOMZ",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            epoch=(1, 50),
            learning_rate=(0.0000002, 0.0002),
            warmup_ratio=(0.01, 0.1),
            weight_decay=(0.001, 1),
            scheduler_name=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank=[8, 16, 32, 64],
                lora_alpha=[8, 16, 32, 64],
                lora_dropout=(0.1, 0.5),
            )
        },
    ),
    "CodeLlama-7B": ModelInfo(
        short_name="CodeLlama_7B",
        base_model_type="CodeLlama",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size=(1, 4),
            epoch=(1, 50),
            max_seq_len=[1024, 2048, 4096],
            learning_rate=(0.0000000001, 0.0002),
            warmup_ratio=(0.01, 0.1),
            weight_decay=(0.001, 1),
            scheduler_name=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank=[8, 16, 32, 64],
                lora_alpha=[8, 16, 32, 64],
                lora_dropout=(0.1, 0.5),
                lora_target_modules=[
                    "self_attn.q_proj",
                    "self_attn.k_proj",
                    "self_attn.v_proj",
                    "self_attn.o_proj",
                    "mlp.gate_proj",
                    "mlp.up_proj",
                    "mlp.down_proj",
                ],
            )
        },
    ),
}

DefaultPostPretrainTrainConfigMapping: Dict[str, Dict[PeftType, TrainConfig]] = {
    "ERNIE-Speed": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.00003,
            max_seq_len=4096,
            peft_type=PeftType.ALL,
        )
    },
    "ERNIE-Bot-turbo-0922": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.00003,
            max_seq_len=4096,
        )
    },
    "Qianfan-Chinese-Llama-2-13B": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            batch_size=192,
            learning_rate=0.000020,
            weight_decay=0.01,
        )
    },
}

tc = TrainConfig(learning_rate=0.333)

# finetune model train type -> default finetune train config
DefaultTrainConfigMapping: Dict[str, Dict[PeftType, TrainConfig]] = {
    "ERNIE-Speed": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.00003,
            max_seq_len=4096,
            logging_steps=1,
            warmup_ratio=0.1,
            weight_decay=0.01,
        ),
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.0003,
            max_seq_len=4096,
            logging_steps=1,
            warmup_ratio=0.10,
            weight_decay=0.0100,
            lora_rank=8,
            lora_all_linear="True",
        ),
    },
    "ERNIE-Bot-turbo-0922": {
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.0003,
            max_seq_len=4096,
            logging_steps=1,
            warmup_ratio=0.10,
            weight_decay=0.0100,
            lora_rank=8,
            lora_all_linear="True",
        ),
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.00003,
            max_seq_len=4096,
            logging_steps=1,
            warmup_ratio=0.1,
            weight_decay=0.01,
        ),
    },
    "ERNIE-Bot-turbo-0725": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.00003,
            max_seq_len=4096,
        ),
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.0003,
            max_seq_len=4096,
        ),
    },
    "ERNIE-Bot-turbo-0704": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.00003,
        ),
        PeftType.PTuning: TrainConfig(
            epoch=1,
            learning_rate=0.03,
        ),
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.00003,
        ),
    },
    "Qianfan-Chinese-Llama-2-7B": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
        ),
        PeftType.PTuning: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
        ),
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
            lora_rank=32,
            lora_alpha=32,
            lora_dropout=0.1,
        ),
    },
    "Qianfan-Chinese-Llama-2-13B": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
        ),
        PeftType.PTuning: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
        ),
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
            lora_rank=32,
            lora_alpha=32,
            lora_dropout=0.1,
        ),
    },
    "Qianfan-Chinese-Llama-2-7B-32K": {
        PeftType.LoRA: TrainConfig(
            epoch=3,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=32768,
            lora_rank=32,
            lora_alpha=32,
            lora_dropout=0.1,
        ),
        PeftType.ALL: TrainConfig(
            epoch=3,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=32768,
        ),
    },
    "ChatGLM2-6B": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
        ),
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
            lora_rank=32,
            lora_alpha=32,
            lora_dropout=0.1,
        ),
    },
    "ChatGLM2-6B-32K": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
        ),
    },
    "Baichuan2-7B-Chat": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
        ),
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
            lora_rank=32,
            lora_alpha=32,
            lora_dropout=0.1,
        ),
    },
    "Baichuan2-13B-Chat": {
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
        ),
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
            lora_rank=32,
            lora_alpha=32,
            lora_dropout=0.1,
        ),
    },
    "BLOOMZ-7B": {
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
            lora_rank=32,
            lora_alpha=32,
            lora_dropout=0.1,
        ),
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
        ),
        PeftType.PTuning: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
        ),
    },
    "CodeLlama-7B": {
        PeftType.LoRA: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
            lora_target_modules=["self_attn.q_proj", "self_attn.v_proj"],
            lora_rank=32,
            lora_alpha=32,
            lora_dropout=0.1,
        ),
        PeftType.ALL: TrainConfig(
            epoch=1,
            learning_rate=0.000001,
            batch_size=1,
            scheduler_name="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,
            max_seq_len=4096,
        ),
    },
}
