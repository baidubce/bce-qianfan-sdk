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
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from qianfan.resources.console import consts as console_consts
from qianfan.trainer.consts import PeftType, ServiceType


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
    extras: Any = None


class DeployConfig(BaseModel):
    name: str = ""
    """
    Service name
    """
    endpoint_prefix: str = ""
    """
    Endpoint custom prefix, will be used to call resource api
    """
    description: str = ""
    """
    description of service
    """
    replicas: int = 1
    """
    replicas for model services, related to the capacity in QPS of model service.
        default set to 1
    """
    pool_type: console_consts.DeployPoolType = (
        console_consts.DeployPoolType.PrivateResource
    )
    """
    resource pool type, public resource will be shared with others.
    """
    service_type: ServiceType
    """
    service type, after deploy, Service could behave like the specific type.
    """
    extras: Any = None


class TrainLimit(BaseModel):
    batch_size_limit: Optional[Tuple[int, int]] = None
    """batch size limit"""
    max_seq_len_options: Optional[Tuple[int, int]] = None
    """max seq len options"""
    epoch_limit: Optional[Tuple[int, int]] = None
    """epoch limit"""
    learning_rate_limit: Optional[Tuple[float, float]] = None
    """learning rate limit"""


class ModelInfo(BaseModel):
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
    "ERNIE-Bot-turbo-0922": ModelInfo(
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
        ),
    ),
    "ERNIE-Bot-turbo-0725": ModelInfo(
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
        ),
        specific_peft_types_params_limit={
            PeftType.ALL: TrainLimit(
                batch_size_limit=(1, 4),
                max_seq_len_options=(4096, 8192),
                epoch_limit=(1, 50),
                learning_rate_limit=(0.00001, 0.00004),
            ),
            PeftType.LoRA: TrainLimit(
                batch_size_limit=(1, 4),
                max_seq_len_options=(4096, 8192),
                epoch_limit=(1, 50),
                learning_rate_limit=(0.00003, 0.001),
            ),
        },
    ),
    "ERNIE-Bot-turbo-0704": ModelInfo(
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
        ),
        specific_peft_types_params_limit={
            PeftType.PTuning: TrainLimit(
                batch_size_limit=(1, 4),
                max_seq_len_options=(4096, 8192),
                epoch_limit=(1, 50),
                learning_rate_limit=(0.003, 0.1),
            ),
            PeftType.ALL: TrainLimit(
                batch_size_limit=(1, 4),
                max_seq_len_options=(4096, 8192),
                epoch_limit=(1, 50),
                learning_rate_limit=(0.00001, 0.00004),
            ),
            PeftType.LoRA: TrainLimit(
                batch_size_limit=(1, 4),
                max_seq_len_options=(4096, 8192),
                epoch_limit=(1, 50),
                learning_rate_limit=(0.00003, 0.001),
            ),
        },
    ),
    "ERNIE-Bot-turbo-0516": ModelInfo(
        base_model_type="ERNIE-Bot-turbo",
        support_peft_types=[PeftType.ALL],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
        ),
    ),
    "Llama-2-7b": ModelInfo(
        base_model_type="Llama-2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
        ),
    ),
    "Llama-2-13b": ModelInfo(
        base_model_type="Llama-2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
        ),
    ),
    "SQLCoder-7B": ModelInfo(
        base_model_type="SQLCoder",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
        ),
    ),
    "ChatGLM2-6B": ModelInfo(
        base_model_type="ChatGLM2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
        ),
    ),
    "Baichuan2-7B": ModelInfo(
        base_model_type="Baichuan2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000000001, 0.0002),
        ),
    ),
    "Baichuan2-13B": ModelInfo(
        base_model_type="Baichuan2",
        support_peft_types=[PeftType.ALL, PeftType.LoRA],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000000001, 0.0002),
        ),
    ),
    "BLOOMZ-7B": ModelInfo(
        base_model_type="BLOOMZ",
        support_peft_types=[PeftType.ALL, PeftType.LoRA, PeftType.PTuning],
        common_params_limit=TrainLimit(
            batch_size_limit=(1, 4),
            max_seq_len_options=(4096, 8192),
            epoch_limit=(1, 50),
            learning_rate_limit=(0.0000002, 0.0002),
        ),
    ),
}

# model train type -> default train config
DefaultTrainConfigMapping: Dict[str, TrainConfig] = {
    "ERNIE-Bot-turbo-0922": TrainConfig(
        epoch=1,
        learning_rate=0.0003,
        max_seq_len=4096,
        peft_type=PeftType.LoRA,
    ),
    "ERNIE-Bot-turbo-0725": TrainConfig(
        epoch=1,
        learning_rate=0.00003,
        max_seq_len=4096,
        peft_type=PeftType.LoRA,
    ),
    "ERNIE-Bot-turbo-0516": TrainConfig(
        epoch=1,
        batch_size=32,
        learning_rate=0.00002,
        peft_type=PeftType.ALL,
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
}
