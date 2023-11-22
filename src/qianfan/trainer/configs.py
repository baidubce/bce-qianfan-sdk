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
from typing import Any, Dict, Optional

from pydantic import BaseModel


class TrainConfig(BaseModel):
    epoch: Optional[int] = None
    batch_size: Optional[int] = None
    learning_rate: Optional[float] = None
    max_seq_len: Optional[int] = None
    peft_type: Optional[str] = None
    """
    parameter efficient FineTuning method, like `LoRA`, `P-tuning`, `ALL`
    """
    trainset_rate: int = 20
    extras: Any = None


class DeployConfig(BaseModel):
    name: str = ""
    endpoint_prefix: str = ""
    description: str = ""
    replicas: int
    pool_type: int
    extras: Any = None


DefaultTrainConfigMapping: Dict[str, TrainConfig] = {
    "ERNIE-Bot-turbo-0725": TrainConfig(
        epoch=1,
        learning_rate=0.00003,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
    "ERNIE-Bot-turbo-0516": TrainConfig(
        epoch=1,
        batch_size=32,
        learning_rate=0.00002,
        peft_type="ALL",
    ),
    "ERNIE-Bot-turbo-0704": TrainConfig(
        epoch=1,
        learning_rate=0.00003,
        peft_type="LoRA",
    ),
    "Llama-2-7b": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.00002,
        peft_type="LoRA",
    ),
    "Llama-2-13b": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.00002,
        peft_type="LoRA",
    ),
    "SQLCoder-7B": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.00002,
        peft_type="LoRA",
    ),
    "ChatGLM2-6B": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.00002,
        peft_type="LoRA",
    ),
    "Baichuan2-13B": TrainConfig(
        epoch=1,
        learning_rate=0.000001,
        peft_type="LoRA",
    ),
    "BLOOMZ-7B": TrainConfig(
        epoch=1,
        batch_size=1,
        learning_rate=0.00002,
        peft_type="LoRA",
    ),
}
