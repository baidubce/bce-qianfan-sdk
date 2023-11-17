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
from typing import Any, Optional

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
    extras: Any = None
    trainsetRate: int = 0


class DeployConfig(BaseModel):
    name: str = ""
    endpoint_prefix: str = ""
    description: str = ""
    replicas: int
    pool_type: int
    extras: Any = None
