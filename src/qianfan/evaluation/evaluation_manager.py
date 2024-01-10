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
import math
import multiprocessing
import time
from concurrent.futures import ALL_COMPLETED, Future, ThreadPoolExecutor, wait
from typing import Any, Dict, List, Optional, Set, Union

from qianfan import get_config
from qianfan.dataset import Dataset, QianfanDataSource
from qianfan.dataset.consts import (
    LLMOutputColumnName,
    NewInputChatColumnName,
    NewInputPromptColumnName,
    OldReferenceColumnName,
)
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
from qianfan.model import Model, Service
from qianfan.resources import Model as ResourceModel
from qianfan.resources.console.consts import EvaluationTaskStatus
from qianfan.utils import log_debug, log_error, log_info, log_warn
from qianfan.utils.pydantic import BaseModel, Field, root_validator
from qianfan.utils.utils import generate_letter_num_random_id


class EvaluationManager(BaseModel):
    """logic control center of evaluation"""

    local_evaluators: Optional[List[LocalEvaluator]] = Field(default=None)
    qianfan_evaluators: Optional[List[QianfanEvaluator]] = Field(default=None)

    @root_validator
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

    def _eval_worker(
        self,
        start: int,
        end: int,
        input: List[Union[str, List[Dict[str, Any]]]],
        reference: List[str],
        output: List[str],
    ) -> List[Dict[str, Any]]:
        result_list: List[Dict[str, Any]] = []
        if start >= end:
            return result_list
        assert self.local_evaluators
        for i in range(start, end):
            result: Dict[str, Any] = {}
            for evaluator in self.local_evaluators:
                result.update(evaluator.evaluate(input[i], reference[i], output[i]))
            result_list.append(result)
        return result_list

    def _run_evaluator_locally(
        self, dataset: Dataset, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        if NewInputPromptColumnName in dataset.col_names():
            ds_dict = dataset.col_list(
                [NewInputPromptColumnName, LLMOutputColumnName, OldReferenceColumnName]
            )
        else:
            ds_dict = dataset.col_list(
                [NewInputChatColumnName, LLMOutputColumnName, OldReferenceColumnName]
            )

        sector_length = math.ceil(len(dataset) / multiprocessing.cpu_count())
        pool = ThreadPoolExecutor()
        future_list: List[Future] = []
        for i in range(multiprocessing.cpu_count()):
            if NewInputPromptColumnName in dataset.col_names():
                future_list.append(
                    pool.submit(
                        self._eval_worker,
                        i * sector_length,
                        min((i + 1) * sector_length, len(dataset)),
                        ds_dict[NewInputPromptColumnName],
                        ds_dict[LLMOutputColumnName],
                        ds_dict[OldReferenceColumnName],
                    )
                )
            else:
                future_list.append(
                    pool.submit(
                        self._eval_worker,
                        i * sector_length,
                        min((i + 1) * sector_length, len(dataset)),
                        ds_dict[NewInputChatColumnName],
                        ds_dict[LLMOutputColumnName],
                        ds_dict[OldReferenceColumnName],
                    )
                )

        wait(future_list, return_when=ALL_COMPLETED)
        result_list: List[Dict[str, Any]] = []
        for future in future_list:
            try:
                result = future.result()
                result_list.extend(result)
            except Exception as e:
                err_msg = (
                    f"an fatal error occurred when evaluate llm output in batch: {e}"
                )
                log_error(err_msg)
                raise e

        return result_list

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
        if len(set(type(llm) for llm in llms)) > 1:
            err_msg = "should use only either Model or Service, not both togather"
            log_error(err_msg)
            raise ValueError(err_msg)

        if self.local_evaluators:
            llm_tags: List[str] = []
            for llm in llms:
                if isinstance(llm, Service):
                    if llm.model:
                        llm_key_str = f"{llm.id}_{llm.endpoint}_{llm.model.name}"
                    else:
                        llm_key_str = f"{llm.id}_{llm.endpoint}"
                elif isinstance(llm, Model):
                    llm_key_str = f"{llm.id}_{llm.version_id}_{llm.name}"
                else:
                    llm_key_str = ""
                llm_tags.append(llm_key_str)

            future_dict: Dict[int, Future] = {}
            pool = ThreadPoolExecutor()
            for index in range(len(llms)):
                llm = llms[index]
                if isinstance(llm, Model):
                    future_dict[index] = pool.submit(
                        dataset.test_using_llm,
                        model_id=llm.id,
                        model_version_id=llm.version_id,
                        **kwargs,
                    )
                elif isinstance(llm, Service):
                    model_name = None if not llm.model else llm.model.name
                    future_dict[index] = pool.submit(
                        dataset.test_using_llm,
                        service_model=model_name,
                        service_endpoint=llm.endpoint,
                        **kwargs,
                    )
            wait(list(future_dict.values()), return_when=ALL_COMPLETED)

            llm_evaluation_result_dict: Dict[int, List[Dict[str, Any]]] = {}
            llm_response_list: Dict[int, List[str]] = {}
            llm_input_list: List[Any] = []
            expected_output_list: List[str] = []

            input_column_name: str = ""

            for index, future in future_dict.items():
                try:
                    result = future.result()
                    llm_response_list[index] = result[LLMOutputColumnName][
                        LLMOutputColumnName
                    ]
                    llm_evaluation_result_dict[index] = self._run_evaluator_locally(
                        result
                    )

                    if not llm_input_list:
                        if NewInputPromptColumnName in result.col_names():
                            llm_input_list = result[NewInputPromptColumnName][
                                NewInputPromptColumnName
                            ]
                            input_column_name = NewInputPromptColumnName
                        else:
                            llm_input_list = result[NewInputChatColumnName][
                                NewInputChatColumnName
                            ]
                            input_column_name = NewInputChatColumnName

                    if not expected_output_list:
                        expected_output_list = result[OldReferenceColumnName][
                            OldReferenceColumnName
                        ]

                except Exception as e:
                    err_msg = (
                        "an error occurred when doing batch inference in"
                        f" evaluation: {e}"
                    )
                    log_warn(err_msg)

            new_response_list: List[List[Dict[str, Any]]] = []
            for index, response_list in llm_response_list.items():
                for inner_index in range(len(response_list)):
                    while len(new_response_list) <= inner_index:
                        new_response_list.append([])
                    eval_result = llm_evaluation_result_dict[index][inner_index]
                    new_response_list[inner_index].append(
                        {
                            "content": response_list[inner_index],
                            "llm_tag": llm_tags[index],
                            **eval_result,
                        }
                    )

            dataset_data = {
                input_column_name: llm_input_list,
                OldReferenceColumnName: expected_output_list,
                "model_content": new_response_list,
            }

            return EvaluationResult(
                result_dataset=Dataset.create_from_pyobj(dataset_data)
            )

        if self.qianfan_evaluators:
            # 检查是否有不支持的实例
            if any([not isinstance(inst, Model) for inst in llms]):
                err_msg = "only Model instance can use QianfanEvaluator"
                log_error(err_msg)
                raise ValueError(err_msg)

            # 检查数据集是否在云上
            if not dataset.is_dataset_located_in_qianfan():
                err_msg = "dataset must be in qianfan, not local storage"
                log_error(err_msg)
                raise ValueError(err_msg)

            # 检查数据集是否是泛文本
            if dataset.is_dataset_generic_text():
                err_msg = "dataset can't be generic text dataset"
                log_error(err_msg)
                raise ValueError(err_msg)

            # 对输入数据做映射
            input_argument_dict: Dict[str, Any] = {}
            for evaluator in self.qianfan_evaluators:
                # 如果处理的是人工评估
                if isinstance(evaluator, QianfanManualEvaluator):
                    input_argument_dict["evalMode"] = (
                        input_argument_dict.get("evalMode", "") + "manual,"
                    )

                    # 超过 4 个指标则截断，对齐平台
                    dimensions = evaluator.evaluation_dimensions[:]
                    if len(evaluator.evaluation_dimensions) > 4:
                        log_warn(
                            "the number of evaluation dimension is more than 4, the"
                            " dimensions will be truncated"
                        )
                        dimensions = dimensions[:4]

                    # 创建指标字典
                    input_dimension_list: List[Dict[str, Any]] = []
                    for dimension in dimensions:
                        input_dimension_dict: Dict[str, Any] = {
                            "dimension": dimension.dimension
                        }
                        if dimension.description:
                            input_dimension_dict["description"] = dimension.description

                        input_dimension_list.append(input_dimension_dict)

                    input_argument_dict["evaluationDimension"] = input_dimension_list

                # 如果处理的是基于规则的评估
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

                    # 添加停用词表
                    if evaluator.stop_words:
                        input_argument_dict["stopWordsPath"] = evaluator.stop_words

                # 如果处理的是基于裁判员的打分
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

            # 提交评估任务
            resp_body = ResourceModel.create_evaluation_task(
                name=f"sdk_eval_{generate_letter_num_random_id(11)}",
                version_info=[
                    {"modelId": model.id, "modelVersionId": model.version_id}
                    for model in model_objs
                ],
                dataset_id=qianfan_data_source.id,
                eval_config=input_argument_dict,
                **kwargs,
            ).body

            eval_id = resp_body["result"]["evalId"]
            task_url = f"https://console.bce.baidu.com/qianfan/modelcenter/model/eval/detail/task/{eval_id}"

            log_info(f"please check webpage {task_url} to get further information")

            # 开始轮询任务进度
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

            # 如果是进入人工评估阶段，则返回空
            # 当前无法获取到评估的单条结果，且无法获取到指标信息
            if eval_state == EvaluationTaskStatus.DoingWithManualBegin:
                log_warn("can't fetch any metrics due to manual mode has been set")
                return None

            result_list = ResourceModel.get_evaluation_result(eval_id)["result"]
            metric_list: Dict[str, Dict[str, Any]] = {
                result["modelName"]: result["effectMetric"] for result in result_list
            }

            # 返回指标信息
            return EvaluationResult(metrics=metric_list)

        return None
