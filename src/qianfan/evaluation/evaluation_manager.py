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
manager which manage whole procedure of evaluation
"""
import time
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, model_validator

from qianfan import get_config
from qianfan.dataset import Dataset, QianfanDataSource
from qianfan.errors import QianfanError
from qianfan.evaluation.consts import QianfanRefereeEvaluatorPromptTemplate
from qianfan.evaluation.evaluation_result import EvaluationResult
from qianfan.evaluation.evaluator import (
    LocalEvaluator,
    QianfanEvaluator,
    QianfanManualEvaluator,
    QianfanRefereeEvaluator,
    QianfanRuleEvaluator,
)
from qianfan.resources import Model as ResourceModel
from qianfan.resources.console.consts import EvaluationTaskStatus
from qianfan.trainer import Model, Service
from qianfan.utils import log_debug, log_error, log_info, log_warn
from qianfan.utils.utils import generate_letter_num_random_id


class EvaluationManager(BaseModel):
    """logic control center of evaluation"""

    local_evaluators: Optional[List[LocalEvaluator]] = Field(default=None)
    qianfan_evaluators: Optional[List[QianfanEvaluator]] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def _check_evaluators(cls, input_dict: Any) -> Any:
        """校验传入的参数"""
        if not isinstance(input_dict, dict):
            err_msg = (
                "the arguments of model validator of EvaluationManager isn't dict,"
                f" rather {type(input_dict)}"
            )
            log_error(err_msg)
            raise ValueError(err_msg)

        local_evaluators = input_dict.get("local_evaluators", None)
        qianfan_evaluators = input_dict.get("qianfan_evaluators", None)

        if not local_evaluators and not qianfan_evaluators:
            # 如果都没设置，则报错抛出
            err_msg = "none of local evaluator and qianfan evaluator has been set"
            log_error(err_msg)
            raise ValueError(err_msg)

        if local_evaluators and qianfan_evaluators:
            # 如果同时设置，则报错抛出
            err_msg = "both local evaluator and qianfan evaluator has been set"
            log_error(err_msg)
            raise ValueError(err_msg)

        if qianfan_evaluators:
            dedup_map: Set[str] = set()
            for evaluator in qianfan_evaluators:
                type_name = f"{type(evaluator)}"
                if type_name in dedup_map:
                    err_msg = f"multiple {type_name} has been set in qianfan_evaluators"
                    log_error(err_msg)
                    raise ValueError

                dedup_map.add(type_name)

        return input_dict

    def eval(
        self, llms: List[Union[Model, Service]], dataset: Dataset, **kwargs: Any
    ) -> Optional[EvaluationResult]:
        """
        Evaluate the performance of models on the dataset.

        Args:
            llms (List[Union[Model, Service]]):
                List of models or service to be evaluated.
            dataset (Dataset):
                The dataset on which models will be evaluated.
            **kwargs (Any):
                Other keyword arguments.

        Returns:
            Optional[EvaluationResult]: Evaluation result of models on the dataset.
        """
        if self.local_evaluators:
            raise NotImplementedError()

        if self.qianfan_evaluators:
            if any([not isinstance(inst, Model) for inst in llms]):
                err_msg = "only Model instance can use QianfanEvaluator"
                log_error(err_msg)
                raise ValueError(err_msg)

            if not dataset.is_dataset_located_in_qianfan():
                err_msg = "dataset must be in qianfan, not local storage"
                log_error(err_msg)
                raise ValueError(err_msg)

            if dataset.is_dataset_generic_text():
                err_msg = "dataset can't be generic text dataset"
                log_error(err_msg)
                raise ValueError(err_msg)

            input_argument_dict: Dict[str, Any] = {}
            for evaluator in self.qianfan_evaluators:
                if isinstance(evaluator, QianfanManualEvaluator):
                    input_argument_dict["evalMode"] = (
                        input_argument_dict.get("evalMode", "") + "manual,"
                    )

                    dimensions = evaluator.evaluation_dimensions[:]
                    if len(evaluator.evaluation_dimensions) > 4:
                        log_warn(
                            "the number of evaluation dimension is more than 4, the"
                            " dimensions will be truncated"
                        )
                        dimensions = dimensions[:4]

                    input_dimension_list: List[Dict[str, Any]] = []
                    for dimension in dimensions:
                        input_dimension_dict: Dict[str, Any] = {
                            "dimension": dimension.dimension
                        }
                        if dimension.description:
                            input_dimension_dict["description"] = dimension.description

                        input_dimension_list.append(input_dimension_dict)

                    input_argument_dict["evaluationDimension"] = input_dimension_list

                if isinstance(evaluator, QianfanRuleEvaluator):
                    input_argument_dict["evalMode"] = (
                        input_argument_dict.get("evalMode", "") + "rule,"
                    )

                    rule_list: List[str] = []
                    if evaluator.using_similarity:
                        rule_list.append("similarity")
                    if evaluator.using_accuracy:
                        rule_list.append("accuracy")

                    if not rule_list:
                        err_msg = (
                            "no rule has been set despite using QianfanRuleEvaluator"
                        )
                        log_error(err_msg)
                        raise ValueError(err_msg)

                    input_argument_dict["scoreModes"] = rule_list

                    if evaluator.stop_words:
                        input_argument_dict["stopWordsPath"] = evaluator.stop_words

                if isinstance(evaluator, QianfanRefereeEvaluator):
                    input_argument_dict["evalMode"] = (
                        input_argument_dict.get("evalMode", "") + "model,"
                    )
                    input_argument_dict["appId"] = evaluator.app_id
                    input_argument_dict["prompt"] = {
                        "templateContent": QianfanRefereeEvaluatorPromptTemplate,
                        "metric": evaluator.prompt_metrics,
                        "steps": evaluator.prompt_steps,
                        "maxScore": evaluator.prompt_max_score,
                    }

            input_argument_dict["evalMode"] = input_argument_dict.get(
                "evalMode", ""
            ).strip(",")

            model_objs: List[Model] = llms  # type: ignore
            qianfan_data_source = dataset.inner_data_source_cache
            assert isinstance(qianfan_data_source, QianfanDataSource)

            resp_body = ResourceModel.create_evaluation_task(
                name=f"sdk_eval_{generate_letter_num_random_id(11)}",
                version_info=[
                    {"modelId": model.id, "modelVersionId": model.version_id}
                    for model in model_objs
                ],
                dataset_id=qianfan_data_source.id,
                eval_config=input_argument_dict,
                dataset_name=qianfan_data_source.name,
                **kwargs,
            ).body

            eval_id = resp_body["result"]["evalId"]
            task_url = f"https://console.bce.baidu.com/qianfan/modelcenter/model/eval/detail/task/{eval_id}"

            log_info(f"please check webpage {task_url} to get further information")

            while True:
                eval_info = ResourceModel.get_evaluation_info(eval_id)
                eval_state = eval_info["result"]["state"]

                log_debug(f"current evaluation task info: {eval_info}")
                log_info(f"current eval_state: {eval_state}")

                if eval_state not in [
                    EvaluationTaskStatus.Pending.value,
                    EvaluationTaskStatus.Doing.value,
                ]:
                    break
                time.sleep(get_config().EVALUATION_ONLINE_POLLING_INTERVAL)

            if eval_state not in [
                EvaluationTaskStatus.DoingWithManualBegin,
                EvaluationTaskStatus.Done,
            ]:
                err_msg = (
                    f"can't finish evaluation task and failed with state {eval_state}"
                )
                log_error(err_msg)
                raise QianfanError(err_msg)

            if eval_state == EvaluationTaskStatus.DoingWithManualBegin:
                log_warn("can't fetch any metrics due to manual mode has been set")
                return None

            result_list = ResourceModel.get_evaluation_result(eval_id)["result"]
            metric_list: Dict[str, Dict[str, Any]] = {
                result["modelName"]: result["effectMetric"] for result in result_list
            }

            return EvaluationResult(metrics=metric_list)

        return None
