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
import os.path
import time
from concurrent.futures import ALL_COMPLETED, Future, ThreadPoolExecutor, wait
from copy import copy
from typing import Any, Dict, List, Optional, Sequence, Set, Union

import pyarrow

from qianfan import get_config
from qianfan.dataset import Dataset
from qianfan.dataset.consts import (
    LLMOutputColumnName,
    LLMTagColumnName,
    OldReferenceColumnName,
)
from qianfan.dataset.data_source import FileDataSource, QianfanDataSource
from qianfan.dataset.data_source.utils import (
    _download_file_from_url_streamly,
)
from qianfan.dataset.schema import EvaluationSchema
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
from qianfan.resources.console.consts import (
    EvaluationResultExportTaskStatus,
    EvaluationTaskStatus,
)
from qianfan.utils import log_debug, log_error, log_info, log_warn
from qianfan.utils.pydantic import BaseModel, Field, root_validator
from qianfan.utils.utils import generate_letter_num_random_id


class EvaluationManager(BaseModel):
    """logic control center of evaluation"""

    local_evaluators: Optional[List[LocalEvaluator]] = Field(default=None)
    qianfan_evaluators: Optional[List[QianfanEvaluator]] = Field(default=None)
    task_id: Optional[str] = Field(default=None)

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

    def _get_eval_task_future(self, dataset: Dataset, **kwargs: Any) -> List[Future]:
        input_column_name = dataset.eval_input_column
        reference_column_name = dataset.reference_column
        output_column_name = dataset.eval_llm_output_column

        ds_dict = dataset.col_list(
            [input_column_name, reference_column_name, output_column_name]
        )

        sector_length = math.ceil(len(dataset) / multiprocessing.cpu_count())
        pool = ThreadPoolExecutor()
        future_list: List[Future] = []
        for i in range(multiprocessing.cpu_count()):
            future_list.append(
                pool.submit(
                    self._eval_worker,
                    i * sector_length,
                    min((i + 1) * sector_length, len(dataset)),
                    ds_dict[input_column_name],
                    ds_dict[reference_column_name],
                    ds_dict[output_column_name],
                )
            )

        return future_list

    def _run_evaluator_locally(
        self, dataset: Dataset, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        future_list = self._get_eval_task_future(dataset, **kwargs)
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

    def _get_llm_tags(self, llms: Sequence[Union[Model, Service]]) -> List[str]:
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

        return llm_tags

    def _get_batch_inference_task_future(
        self, llms: Sequence[Union[Model, Service]], dataset: Dataset, **kwargs: Any
    ) -> Dict[int, Future]:
        future_dict: Dict[int, Future] = {}
        pool = ThreadPoolExecutor()
        for index in range(len(llms)):
            llm = llms[index]
            if isinstance(llm, Model):
                future_dict[index] = pool.submit(
                    dataset.test_using_llm,
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

        return future_dict

    def _get_qianfan_evaluator_configuration_dict(self) -> Dict[str, Any]:
        # 对输入数据做映射
        input_argument_dict: Dict[str, Any] = {}
        assert self.qianfan_evaluators

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
                    err_msg = "no rule has been set despite using QianfanRuleEvaluator"
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

        input_argument_dict["evalMode"] = input_argument_dict.get("evalMode", "").strip(
            ","
        )

        return input_argument_dict

    def _create_qianfan_evaluation_task_and_wait_to_success(
        self,
        llms: Sequence[Union[Model, Service]],
        dataset_id: str,
        eval_config: Dict[str, Any],
        **kwargs: Any,
    ) -> EvaluationTaskStatus:
        model_objs: List[Model] = llms  # type: ignore
        for i in range(len(model_objs)):
            model_objs[i].auto_complete_info()

        resp_body = ResourceModel.create_evaluation_task(
            name=f"sdk_eval_{generate_letter_num_random_id(11)}",
            version_info=[
                {"modelId": model.id, "modelVersionId": model.version_id}
                for model in model_objs
            ],
            dataset_id=dataset_id,
            eval_config=eval_config,
            **kwargs,
        ).body

        eval_id = resp_body["result"]["evalIdStr"]
        task_url = f"https://console.bce.baidu.com/qianfan/modelcenter/model/eval/detail/task/{eval_id}"
        self.task_id = eval_id

        log_info(f"please check webpage {task_url} to get further information")

        # 开始轮询任务进度
        while True:
            eval_info = ResourceModel.get_evaluation_info(eval_id)
            eval_state = EvaluationTaskStatus(eval_info["result"]["state"])

            log_debug(f"current evaluation task info: {eval_info}")
            log_info(f"current eval_state: {eval_state}")

            if eval_state not in [
                EvaluationTaskStatus.Pending,
                EvaluationTaskStatus.Doing,
            ]:
                break
            time.sleep(get_config().EVALUATION_ONLINE_POLLING_INTERVAL)

        if eval_state not in [
            EvaluationTaskStatus.DoingWithManualBegin,
            EvaluationTaskStatus.Done,
        ]:
            err_msg = f"can't finish evaluation task and failed with state {eval_state}"
            log_error(err_msg)
            raise QianfanError(err_msg)

        return eval_state

    def eval_only(
        self,
        dataset: Dataset,
        **kwargs: Any,
    ) -> EvaluationResult:
        """
        running evaluation only on specific dataset

        Args:
            dataset (Dataset):
                dataset which comes from batch inference or be batch-inference like
            **kwargs (Any):
                other keyword arguments.

        Returns:
            EvaluationResult: Evaluation result of models on the dataset.
        """
        if not dataset.eval_input_column or not dataset.eval_llm_output_column:
            err_msg = (
                "either eval_input_column or eval_llm_output_column didn't been set"
            )
            log_error(err_msg)
            raise ValueError(err_msg)

        dataset = copy(dataset)
        if not dataset.reference_column:
            dataset.reference_column = OldReferenceColumnName
            dataset.col_append(
                {OldReferenceColumnName: [None for _ in range(len(dataset))]}
            )

        if not EvaluationSchema().validate(dataset):
            raise ValueError("validate failed before evaluation")

        tmp_ds = Dataset.create_from_pyobj(
            self._run_evaluator_locally(dataset, **kwargs)
        )
        return EvaluationResult(result_dataset=dataset.col_append(tmp_ds.col_list()))

    def eval(
        self, llms: Sequence[Union[Model, Service]], dataset: Dataset, **kwargs: Any
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
            # 大模型的标签列表
            llm_tags = self._get_llm_tags(llms)

            # 检查是否有评估的标准答案列
            # 如果没有，需要复制数据集并且在副本中添加空参考数据列
            # 当且仅当使用的是 Service 对 Completion 补全数据集进行批量推理
            # 且用户没有指定 reference_column 时使用这个逻辑
            if not dataset.reference_column:
                dataset = copy(dataset)
                dataset.reference_column = OldReferenceColumnName
                dataset.col_append(
                    {OldReferenceColumnName: [None for _ in range(len(dataset))]}
                )

            # 首先获取批量评估的结果
            log_info("start to inference in batch during evaluation")
            future_dict = self._get_batch_inference_task_future(llms, dataset, **kwargs)
            wait(list(future_dict.values()), return_when=ALL_COMPLETED)

            # 然后再等待批量推理的结果，并且送去评估

            # 针对单个模型的，每条数据的评估结果字典
            llm_evaluation_result_dict: Dict[int, List[Dict[str, Any]]] = {}
            # 针对单个模型的，每条数据的实际返回列表
            llm_response_list: Dict[int, List[str]] = {}
            # 统一的输入数据列表
            llm_input_list: List[Any] = []
            # 统一的输出数据列表
            expected_output_list: List[str] = []

            input_column_name: str = ""

            for index, future in future_dict.items():
                try:
                    result = future.result()
                    llm_response_list[index] = result[LLMOutputColumnName][
                        LLMOutputColumnName
                    ]
                    # 实际评估的地方
                    log_info(f"start to evaluate llm {index}")
                    llm_evaluation_result_dict[index] = self._run_evaluator_locally(
                        result, **kwargs
                    )

                    assert isinstance(result, Dataset)

                    # 做一些字段填充，只在这两个列表为空的时候进入
                    if not llm_input_list:
                        llm_input_list = result[result.eval_input_column][
                            result.eval_input_column
                        ]
                        assert result.eval_input_column
                        input_column_name = result.eval_input_column

                    if not expected_output_list:
                        expected_output_list = result[result.reference_column][
                            result.reference_column
                        ]

                except Exception as e:
                    err_msg = (
                        "an error occurred when doing batch inference in"
                        f" evaluation: {e}"
                    )
                    log_warn(err_msg)

            # 整合数据，将得到的数据集整合成网页人工评估的数据集格式
            log_info("start to merge evaluation result dataset")
            table_list: List[pyarrow.Table] = []
            for index, response_list in llm_response_list.items():
                index_tag_column = [llm_tags[index] for _ in range(len(response_list))]
                ds = dataset.create_from_pyobj(
                    {
                        LLMTagColumnName: index_tag_column,
                        input_column_name: llm_input_list,
                        OldReferenceColumnName: expected_output_list,
                        LLMOutputColumnName: response_list,
                    }
                )

                metrics_ds = dataset.create_from_pyobj(
                    llm_evaluation_result_dict[index]
                )
                ds.col_append(metrics_ds.col_list())
                table_list.append(ds.inner_table)

            return EvaluationResult(
                result_dataset=Dataset.create_from_pyarrow_table(
                    pyarrow.concat_tables(table_list)
                )
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

            input_argument_dict = self._get_qianfan_evaluator_configuration_dict()
            qianfan_data_source = dataset.inner_data_source_cache
            assert isinstance(qianfan_data_source, QianfanDataSource)

            # 提交评估任务
            eval_state = self._create_qianfan_evaluation_task_and_wait_to_success(
                llms, qianfan_data_source.id, input_argument_dict
            )

            # 如果是进入人工评估阶段，则返回空
            if eval_state == EvaluationTaskStatus.DoingWithManualBegin:
                log_warn("can't fetch any metrics due to manual mode has been set")
                return None

            assert self.task_id
            result_list = ResourceModel.get_evaluation_result(self.task_id)["result"]
            metric_list: Dict[str, Dict[str, Any]] = {
                f'{result["modelName"]}_{result["modelVersion"]}': result[
                    "effectMetric"
                ]
                for result in result_list
            }

            export_task_id = ResourceModel.create_evaluation_result_export_task(
                self.task_id, **kwargs
            )["result"]["exportIDStr"]
            polling_interval = get_config().EXPORT_STATUS_POLLING_INTERVAL

            while True:
                result = ResourceModel.get_evaluation_result_export_task_status(
                    export_task_id
                )["result"]
                task_status = EvaluationResultExportTaskStatus(result["state"])
                if task_status in [
                    EvaluationResultExportTaskStatus.Uploading,
                    EvaluationResultExportTaskStatus.Pending,
                ]:
                    log_info(
                        f"wait evaluation result export task {export_task_id} to be"
                        " completed"
                    )
                    time.sleep(polling_interval)
                    continue

                if task_status == EvaluationResultExportTaskStatus.Fail:
                    err_msg = "evaluation result export failed"
                    log_error(err_msg)
                    raise QianfanError(err_msg)

                if task_status == EvaluationResultExportTaskStatus.Done:
                    log_info("export result succeeded")
                    break

                err_msg = "enter logic unreachable"
                log_error(err_msg)
                raise Exception(err_msg)

            download_url = result["downloadUrl"]
            log_info(f"start to download evaluation result file from {download_url}")

            local_cache_file_path = "tmp.csv"
            try:
                _download_file_from_url_streamly(download_url, local_cache_file_path)

                # 返回指标信息
                return EvaluationResult(
                    result_dataset=Dataset.load(
                        FileDataSource(path=local_cache_file_path),
                        dialect="excel",
                    ),
                    metrics=metric_list,
                )
            finally:
                if os.path.exists(local_cache_file_path):
                    try:
                        os.remove(local_cache_file_path)
                    except Exception:
                        ...

        return None
