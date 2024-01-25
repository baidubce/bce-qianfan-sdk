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
collection of evaluator
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from qianfan.evaluation.consts import (
    QianfanRefereeEvaluatorDefaultMaxScore,
    QianfanRefereeEvaluatorDefaultMetrics,
    QianfanRefereeEvaluatorDefaultSteps,
)
from qianfan.utils import log_error
from qianfan.utils.pydantic import BaseModel, Field, root_validator


class Evaluator(BaseModel, ABC):
    """an class for evaluating single entry"""

    @abstractmethod
    def evaluate(
        self, input: Union[str, List[Dict[str, Any]]], reference: str, output: str
    ) -> Dict[str, Any]:
        """evaluate one entry"""


class LocalEvaluator(Evaluator, ABC):
    """
    Bass class for evaluator running locally

    For user who want to implement their own LocalEvaluator,
    they should overwrite function `evaluate`,
    in which input represents input string or chat history,
    reference as standard answer of input, and
    output for llm output string.

    And the return value should be a Dict
    containing evaluation metrics and
    metric values for single llm output.
    """


class QianfanEvaluator(Evaluator):
    """empty implementation base class for qianfan evaluator"""

    def evaluate(
        self, input: Union[str, List[Dict[str, Any]]], reference: str, output: str
    ) -> Dict[str, Any]:
        # 因为这个方法并不应该被实现，所以此处返回空值
        return {}


class QianfanRefereeEvaluator(QianfanEvaluator):
    """qianfan referee evaluator config class"""

    app_id: int
    prompt_metrics: str = Field(default=QianfanRefereeEvaluatorDefaultMetrics)
    prompt_steps: str = Field(default=QianfanRefereeEvaluatorDefaultSteps)
    prompt_max_score: int = Field(default=QianfanRefereeEvaluatorDefaultMaxScore)


class QianfanRuleEvaluator(QianfanEvaluator):
    """qianfan rule evaluator config class"""

    using_similarity: bool = Field(default=False)
    using_accuracy: bool = Field(default=False)
    stop_words: Optional[str] = Field(default=None)


class ManualEvaluatorDimension(BaseModel):
    """dimension used for manual mode"""

    dimension: str
    description: Optional[str] = Field(default=None)


class QianfanManualEvaluator(QianfanEvaluator):
    """qianfan manual evaluator config class"""

    evaluation_dimensions: List[ManualEvaluatorDimension] = Field(
        default=[ManualEvaluatorDimension(dimension="满意度")]
    )

    @root_validator
    @classmethod
    def dimension_validation(cls, input_dict: Any) -> Any:
        assert isinstance(input_dict, dict)

        dimensions: List[ManualEvaluatorDimension] = input_dict.get(
            "evaluation_dimensions", []
        )
        if not dimensions:
            err_msg = "no dimension has been provided"
            log_error(err_msg)
            raise ValueError(err_msg)

        for i in range(len(dimensions)):
            if dimensions[i].dimension == "满意度":
                if i != 0:
                    dimensions[0], dimensions[i] = dimensions[i], dimensions[0]
                    input_dict["evaluation_dimensions"] = dimensions
                return input_dict

        input_dict["evaluation_dimensions"] = [
            ManualEvaluatorDimension(dimension="满意度")
        ] + dimensions
        return input_dict
