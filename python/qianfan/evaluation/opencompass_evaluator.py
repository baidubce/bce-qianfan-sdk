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


"""
opencompass evaluator evaluator
"""
import inspect
from typing import Any, Dict, List, Union

from qianfan.evaluation.evaluator import LocalEvaluator
from qianfan.utils import log_error
from qianfan.utils.pydantic import root_validator

try:
    from opencompass.openicl.icl_evaluator import BaseEvaluator

    class OpenCompassLocalEvaluator(LocalEvaluator):
        class Config:
            arbitrary_types_allowed = True

        open_compass_evaluator: BaseEvaluator

        @root_validator
        @classmethod
        def _check_open_compass_evaluator(
            cls, values: Dict[str, Any]
        ) -> Dict[str, Any]:
            open_compass_evaluator = values["open_compass_evaluator"]
            signature = inspect.signature(open_compass_evaluator.score)
            params = list(signature.parameters.keys())
            params.sort()
            if params != ["predictions", "references"]:
                raise ValueError(
                    f"unsupported opencompass evaluator {type(open_compass_evaluator)}"
                )
            return values

        def evaluate(
            self, input: Union[str, List[Dict[str, Any]]], reference: str, output: str
        ) -> Dict[str, Any]:
            return self.open_compass_evaluator.score([output], [reference])  # type: ignore

except ModuleNotFoundError:

    class OpenCompassLocalEvaluator(LocalEvaluator):  # type: ignore
        def __init__(self, **kwargs: Any) -> None:
            log_error(
                "opencompass not found in your packages, OpenCompassLocalEvaluator not"
                " available now. if you want to use it please execute 'pip install"
                " opencompass'"
            )
            raise ModuleNotFoundError("opencompass not found")
