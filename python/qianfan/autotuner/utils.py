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

from typing import Any, Dict, List

from qianfan.utils.pydantic import BaseModel

Config = Dict[str, Any]
ConfigList = List[Config]
Metrics = Dict[str, Any]


class TrialResult(BaseModel):
    """
    Result of each trial.
    """

    turn: int
    """
    Turn of this trial in the whole tuning process.
    """
    config: Config
    """
    Config of this trial which is suggested by the suggestor.
    """
    metrics: Metrics
    """
    The metrics of this config which is output by the runner.
    """
    custom_results: Any
    """
    Custom results of this trial.
    
    This is output by the runner and be used to store data such 
    as model outputs that are not directly tied to the metrics 
    but aid in observing the results.
    """
