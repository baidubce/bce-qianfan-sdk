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
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from qianfan.config import encoding
from qianfan.errors import InvalidArgumentError
from qianfan.trainer.consts import PeftType
from qianfan.utils import log_error, log_warn
from qianfan.utils.pydantic import BaseModel

T = TypeVar("T")


class TrainConfig(BaseModel):
    epoch: Optional[int] = None
    """
    epoch number: differ from models
    """
    batch_size: Optional[int] = None
    """
    batch size: differ from models
    """
    learning_rate: Optional[float] = None
    """
    learning rate: differ from models
    """
    max_seq_len: Optional[int] = None
    """
    max_seq_len: differ from models
    """
    peft_type: Optional[Union[str, PeftType]] = None
    """
    parameter efficient FineTuning method, like `LoRA`, `P-tuning`, `ALL`
    """
    trainset_rate: int = 20
    """
    rate for dataset to spilt 
    """
    logging_steps: Optional[int] = None
    """log saving interval steps"""
    warmup_ratio: Optional[float] = None
    """warmup ratio"""
    weight_decay: Optional[float] = None
    """normalization params"""
    lora_rank: Optional[int] = None
    """loRA rank"""
    lora_all_linear: Optional[str] = None
    """loRA all linear layer"""
    scheduler_name: Optional[str] = None
    """for learning rate schedule"""
    lora_alpha: Optional[int] = None
    """LoRA scaling params"""
    lora_dropout: Optional[float] = None
    """loRA dropout"""

    extras: Dict[str, Any] = {}

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

    # 后期考虑迁移到pydantic做动态校验，当前需要根据train_type和train_limit做校验
    def validate_config(self, train_limit: "TrainLimit") -> bool:
        res = True
        res &= self._validate_range(self.epoch, [train_limit.epoch_limit], "epoch")
        res &= self._validate_range(
            self.batch_size, [train_limit.batch_size_limit], "batch_size"
        )
        res &= self._validate_range(
            self.learning_rate, [train_limit.learning_rate_limit], "learning_rate"
        )
        res &= self._validate_options(
            self.max_seq_len, train_limit.max_seq_len_options, "max_seq_len"
        )
        res &= self._validate_range(
            self.logging_steps, [train_limit.log_steps_limit], "logging_steps"
        )
        res &= self._validate_range(
            self.warmup_ratio, [train_limit.warmup_ratio_limit], "warmup_ratio"
        )
        res &= self._validate_range(
            self.weight_decay, [train_limit.weight_decay_limit], "weight_decay"
        )
        res &= self._validate_options(
            self.lora_alpha, train_limit.lora_alpha_options, "lora_alpha"
        )
        res &= self._validate_options(
            self.lora_rank, train_limit.lora_rank_options, "lora_rank"
        )
        res &= self._validate_range(
            self.lora_dropout, [train_limit.lora_dropout_limit], "lora_dropout"
        )
        res &= self._validate_options(
            self.scheduler_name, train_limit.scheduler_name_options, "scheduler_name"
        )
        return res

    def _validate_range(
        self, value: Any, limit_ranges: List[Optional[Tuple[T, T]]], field_name: str
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
        for r in limit_ranges:
            if r is None:
                continue
            if r[0] > value or r[1] < value:
                log_warn(
                    f"train_config current {field_name} is {value}:"
                    f" but suggested {field_name} is in {r}"
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

    def validate_valid_fields(self, limit: "TrainLimit") -> str:
        """
        return invalid field name if value is not in limit.supported_hyper_params
        return "" if all fields are valid.
        """
        supported_fields = limit.supported_hyper_params
        for field in self.dict(exclude_none=True):
            if field in ["peft_type", "extras", "trainset_rate"]:
                continue
            if field not in supported_fields:
                log_warn(
                    f"train_config hyper params '{field}' is not in supported_params:"
                    f" {supported_fields}"
                )
                return field
        return ""


class TrainLimit(BaseModel):
    batch_size_limit: Optional[Tuple[int, int]] = None
    """batch size limit"""
    max_seq_len_options: Optional[List[int]] = None
    """max seq len options"""
    epoch_limit: Optional[Tuple[int, int]] = None
    """epoch limit"""
    learning_rate_limit: Optional[Tuple[float, float]] = None
    """learning rate limit"""
    log_steps_limit: Optional[Tuple[int, int]] = None
    """log steps limit"""
    warmup_ratio_limit: Optional[Tuple[float, float]] = None
    """warmup_ratio limit"""
    weight_decay_limit: Optional[Tuple[float, float]] = None
    """weight_decay limit"""
    lora_rank_options: Optional[List[int]] = None
    """loRA rank options"""
    lora_alpha_options: Optional[List[int]] = None
    """loRA alpha limit"""
    lora_dropout_limit: Optional[Tuple[float, float]] = None
    """loRA dropout limit"""
    scheduler_name_options: Optional[List[str]] = None
    """scheduler name options"""

    supported_hyper_params: List[str] = []
    """supported hyper params"""

    def __or__(self, other: Any) -> "TrainLimit":
        assert isinstance(other, TrainLimit)
        # 使用copy模块深拷贝a的数据，避免修改原始数据
        merged_data = copy.deepcopy(self.dict())

        # 遍历b的字段，如果a中的值为None，则取b的值
        for field, value in other.dict().items():
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


# model train type -> default train config
ModelInfoMapping: Dict[str, ModelInfo] = {
    "ERNIE-Speed": ModelInfo(
        short_name="ERNIE_Speed",
        base_model_type="ERNIE-Speed",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[4096, 8192],
            epoch_limit=(1, 50),
            log_steps_limit=(1, 100),
            warmup_ratio_limit=(0.01, 0.5),
            weight_decay_limit=(0.0001, 0.1),
        ),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                learning_rate_limit=(0.00001, 0.00004),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "log_steps",
                    "warmup_ratio",
                    "weight_decay",
                ],
            ),
            PeftType.LoRA: TrainLimit(
                learning_rate_limit=(0.00003, 0.001),
                lora_rank_options=[2, 4, 8],
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "log_steps",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_all_linear",
                ],
            ),
        },
    ),
    "ERNIE-Bot-turbo-0922": ModelInfo(
        short_name="turbo_0922",
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[4096, 8192],
            epoch_limit=(1, 50),
            log_steps_limit=(1, 100),
            warmup_ratio_limit=(0.01, 0.5),
            weight_decay_limit=(0.0001, 0.1),
        ),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                learning_rate_limit=(0.00001, 0.00004),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "log_steps",
                    "warmup_ratio",
                    "weight_decay",
                ],
            ),
            PeftType.LoRA: TrainLimit(
                learning_rate_limit=(0.00003, 0.001),
                lora_rank_options=[2, 4, 8],
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "log_steps",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_all_linear",
                ],
            ),
        },
    ),
    "ERNIE-Bot-turbo-0725": ModelInfo(
        short_name="turbo_0725",
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            max_seq_len_options=[4096, 8192],
            epoch_limit=(1, 50),
        ),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                learning_rate_limit=(0.00001, 0.00004),
                supported_hyper_params=["epoch", "learning_rate", "max_seq_len"],
            ),
            PeftType.LoRA: TrainLimit(
                learning_rate_limit=(0.00003, 0.001),
                supported_hyper_params=["epoch", "learning_rate", "max_seq_len"],
            ),
        },
    ),
    "ERNIE-Bot-turbo-0704": ModelInfo(
        short_name="turbo_0704",
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            epoch_limit=(1, 50),
        ),
        specific_peft_types_params_limit={
            PeftType.PTuning: TrainLimit(
                learning_rate_limit=(0.003, 0.1),
                supported_hyper_params=["epoch", "learning_rate"],
            ),
            PeftType.ALL: TrainLimit(
                learning_rate_limit=(0.00001, 0.00004),
                supported_hyper_params=["epoch", "learning_rate"],
            ),
            PeftType.LoRA: TrainLimit(
                learning_rate_limit=(0.00003, 0.001),
                supported_hyper_params=["epoch", "learning_rate"],
            ),
        },
    ),
    "Llama-2-7b": ModelInfo(
        short_name="Llama2_7b",
        base_model_type="Llama-2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[1024, 2048, 4096],
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
            scheduler_name_options=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
            weight_decay_limit=(0.001, 1),
            warmup_ratio_limit=(0.01, 0.1),
            supported_hyper_params=[
                "epoch",
                "learning_rate",
                "max_seq_len",
                "batch_size",
                "scheduler_name",
                "warmup_ratio",
                "weight_decay",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank_options=[8, 16, 32, 64],
                lora_alpha_options=[8, 16, 32, 64],
                lora_dropout_limit=(0.1, 0.5),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "batch_size",
                    "scheduler_name",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_alpha",
                    "lora_dropout",
                ],
            ),
        },
    ),
    "Llama-2-13b": ModelInfo(
        short_name="Llama2_13b",
        base_model_type="Llama-2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[1024, 2048, 4096],
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
            scheduler_name_options=[
                "linear",
                "cosine",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
            weight_decay_limit=(0.001, 1),
            warmup_ratio_limit=(0.01, 0.1),
            supported_hyper_params=[
                "epoch",
                "learning_rate",
                "max_seq_len",
                "batch_size",
                "scheduler_name",
                "warmup_ratio",
                "weight_decay",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank_options=[8, 16, 32, 64],
                lora_alpha_options=[8, 16, 32, 64],
                lora_dropout_limit=(0.1, 0.5),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "batch_size",
                    "scheduler_name",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_alpha",
                    "lora_dropout",
                ],
            ),
        },
    ),
    "SQLCoder-7B": ModelInfo(
        short_name="SQLCoder_7B",
        base_model_type="SQLCoder",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[4096, 8192],
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
            supported_hyper_params=[
                "epoch",
                "learning_rate",
                "max_seq_len",
                "batch_size",
                "scheduler_name",
                "warmup_ratio",
                "weight_decay",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank_options=[8, 16, 32, 64],
                lora_alpha_options=[8, 16, 32, 64],
                lora_dropout_limit=(0.1, 0.5),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "batch_size",
                    "scheduler_name",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_alpha",
                    "lora_dropout",
                ],
            ),
        },
    ),
    "ChatGLM2-6B": ModelInfo(
        short_name="GLM2_6B",
        base_model_type="ChatGLM2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[4096, 8192],
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
            supported_hyper_params=[
                "epoch",
                "learning_rate",
                "max_seq_len",
                "batch_size",
                "scheduler_name",
                "warmup_ratio",
                "weight_decay",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                lora_rank_options=[8, 16, 32, 64],
                lora_alpha_options=[8, 16, 32, 64],
                lora_dropout_limit=(0.1, 0.5),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "batch_size",
                    "scheduler_name",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_alpha",
                    "lora_dropout",
                ],
            ),
        },
    ),
    "ChatGLM2-6B-32K": ModelInfo(
        short_name="GLM2_6B_32K",
        base_model_type="ChatGLM2",
        support_peft_types=[PeftType.ALL],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[4096, 8192],
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
            supported_hyper_params=[
                "epoch",
                "learning_rate",
                "scheduler_name",
                "warmup_ratio",
                "weight_decay",
            ],
        ),
    ),
    "Baichuan2-7B": ModelInfo(
        short_name="Baichuan2_7B",
        base_model_type="Baichuan2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[4096, 8192],
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000000001, 0.0002),
            supported_hyper_params=[
                "epoch",
                "learning_rate",
                "max_seq_len",
                "batch_size",
                "scheduler_name",
                "warmup_ratio",
                "weight_decay",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                batch_size_limit=(1, 4),
                max_seq_len_options=[4096, 8192],
                epoch_limit=(1, 50),
                learning_rate_limit=(0.0000000001, 0.0002),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "batch_size",
                    "scheduler_name",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_alpha",
                    "lora_dropout",
                ],
            )
        },
    ),
    "Baichuan2-13B": ModelInfo(
        short_name="Baichuan2_13B",
        base_model_type="Baichuan2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[4096, 8192],
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000000001, 0.0002),
            supported_hyper_params=[
                "epoch",
                "learning_rate",
                "max_seq_len",
                "scheduler_name",
                "warmup_ratio",
                "weight_decay",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                batch_size_limit=(1, 4),
                max_seq_len_options=[4096, 8192],
                epoch_limit=(1, 50),
                learning_rate_limit=(0.0000000001, 0.0002),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "batch_size",
                    "scheduler_name",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_alpha",
                    "lora_dropout",
                ],
            )
        },
    ),
    "BLOOMZ-7B": ModelInfo(
        short_name="BLOOMZ_7B",
        base_model_type="BLOOMZ",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=[4096, 8192],
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
            supported_hyper_params=[
                "epoch",
                "learning_rate",
                "max_seq_len",
                "batch_size",
                "scheduler_name",
                "warmup_ratio",
                "weight_decay",
                "lora_rank",
                "lora_alpha",
                "lora_dropout",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                batch_size_limit=(1, 4),
                max_seq_len_options=[4096, 8192],
                epoch_limit=(1, 50),
                learning_rate_limit=(0.0000000001, 0.0002),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "batch_size",
                    "scheduler_name",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_alpha",
                    "lora_dropout",
                ],
            )
        },
    ),
    "CodeLlama-7B": ModelInfo(
        short_name="CodeLlama_7B",
        base_model_type="CodeLlama",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000000001, 0.0002),
            supported_hyper_params=[
                "epoch",
                "learning_rate",
                "max_seq_len",
                "batch_size",
                "scheduler_name",
                "warmup_ratio",
                "weight_decay",
            ],
        ),
        specific_peft_types_params_limit={
            PeftType.LoRA: TrainLimit(
                batch_size_limit=(1, 4),
                max_seq_len_options=[4096, 8192],
                epoch_limit=(1, 50),
                learning_rate_limit=(0.0000000001, 0.0002),
                supported_hyper_params=[
                    "epoch",
                    "learning_rate",
                    "max_seq_len",
                    "batch_size",
                    "scheduler_name",
                    "warmup_ratio",
                    "weight_decay",
                    "lora_rank",
                    "lora_alpha",
                    "lora_dropout",
                    "lora_target_modules",
                ],
            )
        },
    ),
}

# model train type -> default train config
DefaultTrainConfigMapping: Dict[str, TrainConfig] = {
    "ERNIE-Speed": TrainConfig(
        epoch=1,
        learning_rate=0.0003,
        max_seq_len=4096,
        peft_type=PeftType.LoRA,
        logging_steps=1,
        warmup_ratio=0.10,
        weight_decay=0.0100,
        lora_rank=8,
        lora_all_linear="True",
    ),
    "ERNIE-Bot-turbo-0922": TrainConfig(
        epoch=1,
        learning_rate=0.0003,
        max_seq_len=4096,
        peft_type=PeftType.LoRA,
        logging_steps=1,
        warmup_ratio=0.10,
        weight_decay=0.0100,
        lora_rank=8,
        lora_all_linear="True",
    ),
    "ERNIE-Bot-turbo-0725": TrainConfig(
        epoch=1,
        learning_rate=0.00003,
        max_seq_len=4096,
        peft_type=PeftType.LoRA,
    ),
    "ERNIE-Bot-turbo-0704": TrainConfig(
        epoch=1,
        learning_rate=0.00003,
        peft_type=PeftType.LoRA,
    ),
    "Llama-2-7b": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.00002,
        peft_type=PeftType.LoRA,
    ),
    "Llama-2-13b": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.00002,
        peft_type=PeftType.LoRA,
    ),
    "SQLCoder-7B": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.00002,
        peft_type=PeftType.LoRA,
    ),
    "ChatGLM2-6B": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.00002,
        peft_type=PeftType.LoRA,
    ),
    "ChatGLM2-6B-32K": TrainConfig(
        epoch=1,
        learning_rate=0.00002,
        peft_type=PeftType.ALL,
    ),
    "Baichuan2-7B": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.000001,
        peft_type=PeftType.LoRA,
    ),
    "Baichuan2-13B": TrainConfig(
        epoch=1,
        learning_rate=0.000001,
        peft_type=PeftType.LoRA,
    ),
    "BLOOMZ-7B": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.00002,
        peft_type=PeftType.LoRA,
    ),
    "CodeLlama-7B": TrainConfig(
        epoch=1,
        learning_rate=0.000001,
        batch_size=1,
        peft_type=PeftType.LoRA,
    ),
}
