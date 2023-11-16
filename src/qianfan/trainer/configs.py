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
