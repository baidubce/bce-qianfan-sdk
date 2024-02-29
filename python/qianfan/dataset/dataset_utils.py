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
utilities dataset needs
"""
import time
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

import requests

from qianfan import ChatCompletion, Completion, QfResponse, get_config
from qianfan.common import Prompt
from qianfan.dataset.data_source import DataSource, QianfanDataSource
from qianfan.dataset.schema import (
    QianfanGenericText,
    QianfanQuerySet,
    QianfanSortedConversation,
    QianfanText2Image,
    Schema,
)
from qianfan.errors import QianfanError, RequestError
from qianfan.resources import Data, Model
from qianfan.resources.console.consts import (
    DataTemplateType,
    ETLTaskStatus,
    EvaluationTaskStatus,
)
from qianfan.utils import log_debug, log_error, log_info, log_warn
from qianfan.utils.utils import generate_letter_num_random_id


def _check_online_data_process_result(etl_id: str) -> Optional[Union[bool, int]]:
    """
    check etl task result using etl task id

    Args:
        etl_id (str):
            etl task id
    Returns:
        Optional[Union[bool, int]]: return None when task is still on processing.
            return False if task failed and return dataset id which contains data
            after clean
    """
    result = Data.get_dataset_etl_task_info(etl_id)["result"]
    if result["processStatus"] == ETLTaskStatus.Finished.value:
        log_info(f"data etl task {etl_id} succeeded")
        return result["destDatasetStrId"]
    if result["processStatus"] == ETLTaskStatus.Running.value:
        log_info(f"data etl task {etl_id} running")
        return None
    if result["processStatus"] == ETLTaskStatus.Paused.value:
        log_warn(f"etl task {etl_id} paused")
        return None
    if result["processStatus"] in [
        ETLTaskStatus.Failed.value,
        ETLTaskStatus.Interrupted.value,
    ]:
        log_warn(
            f"etl task {etl_id} terminated with status code: {result['processStatus']}"
        )
        return False

    return False


def _create_a_dataset_etl_task(
    origin_data_source: Optional[DataSource],
    operator_dict: Dict[str, List[Dict[str, Any]]],
) -> Tuple[str, str]:
    assert isinstance(origin_data_source, QianfanDataSource)

    log_info("create a new dataset group and dataset")
    new_data_source = QianfanDataSource.create_bare_dataset(
        name=f"etl_result_set_{generate_letter_num_random_id()}",
        template_type=origin_data_source.template_type,
        storage_type=origin_data_source.storage_type,
        storage_id=origin_data_source.storage_id,
        storage_path=origin_data_source.storage_raw_path,
        ak=origin_data_source.ak,
        sk=origin_data_source.sk,
    )

    log_debug(
        f"new dataset id: {new_data_source.id} , and name: {new_data_source.name}"
    )
    log_info("new dataset group and dataset created, start creating etl task")

    etl_id: str = Data.create_dataset_etl_task(
        source_dataset_id=origin_data_source.id,
        destination_dataset_id=new_data_source.id,
        operations=operator_dict,
    ).body["result"]

    log_info(f"created etl task id: {etl_id}")
    return etl_id, new_data_source.id


def _get_qianfan_schema(source: QianfanDataSource) -> Schema:
    """推断获取 Schema"""
    template_type = source.template_type
    if template_type == DataTemplateType.SortedConversation:
        return QianfanSortedConversation()
    if template_type == DataTemplateType.NonSortedConversation:
        return QianfanSortedConversation()
    if template_type == DataTemplateType.GenericText:
        return QianfanGenericText()
    if template_type == DataTemplateType.QuerySet:
        return QianfanQuerySet()
    if template_type == DataTemplateType.Text2Image:
        return QianfanText2Image()

    error = ValueError(f"schema didn't find for template type {template_type}")
    log_error(str(error))
    raise error


def log_latency_info(result: QfResponse, index: int, stream_index: int = 1) -> Tuple:
    if result.statistic:
        request_latency = result.statistic.get("request_latency", None)
        if "first_token_latency" in result.statistic:
            first_token_latency = result.statistic["first_token_latency"]
            total_latency = result.statistic["total_latency"]
            log_debug(
                f"数据 {index} 的第 {stream_index} 片回包请求响应时延:"
                f" {request_latency}, 包的首 token 时延: {first_token_latency}"
            )
            return request_latency, first_token_latency, total_latency

        log_debug(
            f"数据 {index} 的第 {stream_index} 片回包请求响应时延: {request_latency}"
        )
        return tuple([request_latency])

    return tuple()


def _batch_do_on_service(
    service: Union[ChatCompletion, Completion],
    input_list: Union[List[str], List[List[Dict[str, Any]]]],
    *args: Any,
    **kwargs: Any,
) -> Tuple[List[str], List[float], List[float]]:
    if "prompt_template" in kwargs:
        kwargs.pop("prompt_template")
    output_list: List[str] = []
    request_latency_list: List[float] = []
    first_token_latency_list: List[float] = []
    results = service.batch_do(input_list, *args, **kwargs).results()  # type: ignore
    for idx in range(len(results)):
        result = results[idx]
        if isinstance(result, QfResponse):
            output_list.append(result.body["result"])
            latencies = log_latency_info(result, idx)
            request_latency_list.append(latencies[0])
        elif isinstance(result, Exception):
            log_warn(
                "an exception has occurred during batch requesting and its"
                f" result will be empty string. exception: {result}\ninput:"
                f" {input_list[idx]}"
            )
            output_list.append("")
        else:
            result_str = ""
            index = 0
            first_token_latency: float = 0
            total_latency: float = 0
            for r in result:
                result_str += r.body["result"]
                index += 1
                latencies = log_latency_info(r, idx, index)
                first_token_latency, total_latency = latencies[1], latencies[2]
            output_list.append(result_str)
            request_latency_list.append(total_latency)
            first_token_latency_list.append(first_token_latency)

    return output_list, request_latency_list, first_token_latency_list


async def _async_batch_do_on_service(
    service: Union[ChatCompletion, Completion],
    input_list: Union[List[str], List[List[Dict[str, Any]]]],
    *args: Any,
    **kwargs: Any,
) -> Tuple[List[str], List[float], List[float]]:
    if "prompt_template" in kwargs:
        kwargs.pop("prompt_template")
    output_list: List[str] = []
    request_latency_list: List[float] = []
    first_token_latency_list: List[float] = []
    results = await service.abatch_do(input_list, *args, **kwargs)  # type: ignore
    for idx in range(len(results)):
        result = results[idx]
        if isinstance(result, QfResponse):
            output_list.append(result.body["result"])
            latencies = log_latency_info(result, idx)
            request_latency_list.append(latencies[0])
        elif isinstance(result, Exception):
            log_warn(
                "an exception has occurred during batch requesting and its"
                f" result will be empty string. exception: {result}\ninput:"
                f" {input_list[idx]}"
            )
            output_list.append("")
        else:
            result_str = ""
            index = 0
            first_token_latency: float = 0
            total_latency: float = 0
            async for r in result:
                result_str += r.body["result"]
                index += 1
                latencies = log_latency_info(r, idx, index)
                first_token_latency, total_latency = latencies[1], latencies[2]
            output_list.append(result_str)
            request_latency_list.append(total_latency)
            first_token_latency_list.append(first_token_latency)

    return output_list, request_latency_list, first_token_latency_list


def _list_cloud_data(
    data_source: Optional[DataSource],
    by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None,
    **kwargs: Any,
) -> Any:
    assert isinstance(data_source, QianfanDataSource)
    log_info(f"list qianfan dataset data by {by}")

    if isinstance(by, str):
        message = "can't get entity by string from qianfan"
        log_error(message)
        raise ValueError(message)
    elif isinstance(by, (list, tuple)):
        message = "can't get entity by sequence from qianfan"
        log_error(message)
        raise ValueError(message)

    args: Dict[str, Any] = {"dataset_id": data_source.id}

    if isinstance(by, int):
        args["offset"] = by
        args["page_size"] = 1
    elif isinstance(by, slice):
        args["offset"] = by.start
        args["page_size"] = by.stop - by.start + 1

    log_debug(f"request qianfan dataset list args: {args}")
    resp = Data.list_all_entity_in_dataset(**{**kwargs, **args})["result"]["items"]
    log_info("received dataset list from qianfan dataset")
    log_debug(f"request qianfan dataset list response items: {resp}")
    result = [
        {"entity_id": record["id"], "entity_url": record["url"]} for record in resp
    ]

    for elem in result:
        for i in range(get_config().GET_ENTITY_CONTENT_FAILED_RETRY_TIMES):
            log_info(f"retrieve single entity from {elem['entity_url']} in try {i}")
            resp = requests.get(elem["entity_url"])
            if resp.status_code == 200:
                break
            log_warn(f"request url {elem['entity_url']} failed, retry")

        if resp.status_code != 200:
            message = (
                f"request content of entity {elem['entity_id']} from"
                f" {elem['entity_url']} failed"
            )
            log_error(message)
            raise RequestError(message)

        log_info(
            f"retrieve single entity from {elem['entity_url']} succeeded, with"
            f" content: {resp.text}"
        )
        elem.pop("entity_url")
        elem["entity_content"] = resp.text

    return result


def _wait_evaluation_finished(eval_id: str) -> str:
    log_info(f"start to polling status of evaluation task {eval_id}")

    while True:
        eval_info = Model.get_evaluation_info(eval_id)
        eval_state = eval_info["result"]["state"]

        log_debug(f"current evaluation task info: {eval_info}")
        log_info(f"current eval_state: {eval_state}")

        if eval_state not in [
            EvaluationTaskStatus.Pending.value,
            EvaluationTaskStatus.Doing.value,
        ]:
            break
        time.sleep(get_config().BATCH_RUN_STATUS_POLLING_INTERVAL)

    if eval_state not in [
        EvaluationTaskStatus.DoingWithManualBegin,
        EvaluationTaskStatus.Done,
    ]:
        err_msg = f"can't finish evaluation task and failed with state {eval_state}"
        log_error(err_msg)
        raise QianfanError(err_msg)

    result_dataset_id = eval_info["result"]["evalStandardConf"]["resultDatasetIdStr"]
    log_info(f"get result dataset id {result_dataset_id}")

    return result_dataset_id


def _start_an_evaluation_task_for_model_batch_inference(
    data_source: Optional[DataSource],
    model_id: str,
    model_version_id: str,
    **kwargs: Any,
) -> str:
    assert isinstance(data_source, QianfanDataSource)

    log_info("start to create evaluation task in model")

    resp = Model.create_evaluation_task(
        name=f"model_run_{generate_letter_num_random_id()}",
        version_info=[
            {
                "modelId": model_id,
                "modelVersionId": model_version_id,
            }
        ],
        dataset_id=data_source.id,
        eval_config={
            "evalMode": "manual",
            "evaluationDimension": [
                {"dimension": "满意度"},
            ],
        },
        dataset_name=data_source.name,
        **kwargs,
    ).body

    eval_id = resp["result"]["evalIdStr"]

    log_debug(f"create evaluation task in model response: {resp}")
    result_dataset_id = _wait_evaluation_finished(eval_id)
    log_debug("evaluation task completed")

    return result_dataset_id


def _check_and_generate_service(
    input_columns: Optional[List[str]] = None,
    service_model: Optional[str] = None,
    service_endpoint: Optional[str] = None,
    is_chat_service: bool = False,
    **kwargs: Any,
) -> Union[ChatCompletion, Completion]:
    if not input_columns:
        err_msg = "no input column has been set"
        log_error(err_msg)
        raise ValueError(err_msg)

    prompt_template: Optional[Prompt] = kwargs.get("prompt_template", None)

    if prompt_template:
        log_info("prompt template detected, start to check template variables")
        for column in input_columns:
            if column not in prompt_template.variables:
                err_msg = f"input column {column} not in prompt template"
                log_error(err_msg)
                raise ValueError(err_msg)

    service: Union[ChatCompletion, Completion]
    if is_chat_service:
        service = ChatCompletion(service_model, service_endpoint)
    else:
        service = Completion(service_model, service_endpoint)

    return service


def _extract_string(data: Union[str, Iterator[str]]) -> str:
    if isinstance(data, str):
        return data
    elif hasattr(data, "__iter__"):
        for item in data:
            return _extract_string(item)
    return ""
