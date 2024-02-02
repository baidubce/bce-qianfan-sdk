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
schema for validation
currently qianfan schema only
"""
import functools
from abc import ABC, abstractmethod
from typing import Any, Callable

from qianfan.dataset.consts import (
    LLMOutputColumnName,
    NewInputChatColumnName,
    NewInputPromptColumnName,
    OldReferenceColumnName,
)
from qianfan.dataset.table import Table
from qianfan.utils import log_error, log_info


def _data_format_converter(func: Callable) -> Callable:
    @functools.wraps(func)
    def inner(schema: Schema, table: Table, *args: Any, **kwargs: Any) -> bool:
        if table.is_dataset_packed():
            log_info("unpack dataset before validating")
            table.unpack()
            result = func(schema, table, *args, **kwargs)
            log_info("pack dataset after validation")
            table.pack()
            return result

        return func(schema, table, *args, **kwargs)

    return inner


class Schema(ABC):
    @abstractmethod
    def validate(self, table: Table) -> bool:
        """
        validate a dataset.Table object
        currently check field and type only, not content in table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """


class QianfanSchema(Schema):
    def __init__(self) -> None:
        """
        initialize a new Schema instance
        """
        # 千帆使用，用于作为返回值，表示是否是带标注的数据
        self.is_annotated: bool = False

    def validate(self, table: Table) -> bool:
        return self.is_annotated


# 无排序对话
class QianfanNonSortedConversation(QianfanSchema):
    """validator for non-sorted, conversational dataset"""

    @_data_format_converter
    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        if table.row_number() == 0:
            log_error("no data in table")
            return False

        col_names = table.col_names()

        # 本地单轮对话对接千帆的校验规则
        if "prompt" not in col_names:
            log_error("no prompt column in dataset column")
            return False
        if table.inner_table.column("prompt").null_count:
            log_error("prompt column has empty data in dataset column")
            return False

        if "response" in col_names:
            if table.inner_table.column("response").null_count:
                log_error("response column has empty data in dataset column")
                return False
            response_list = table.col_list("response")["response"]
            for index in range(len(response_list)):
                response_record = response_list[index]
                if not (
                    isinstance(response_record, list)
                    and len(response_record) == 1
                    and isinstance(response_record[0], list)
                    and len(response_record[0]) == 1
                    and isinstance(response_record[0][0], str)
                    and response_record[0][0]
                ):
                    log_error(
                        f"response illegal in dataset row {index}. response data:"
                        f" {response_record}\n"
                        "for accurate dataset format, please check"
                        "https://cloud.baidu.com/doc/WENXINWORKSHOP/s/yliu6bqzw"
                        "#%E6%9C%89%E6%A0%87%E6%B3%A8%E4%BF%A1%E6%81%AF"
                        "-%E6%9C%AC%E5%9C%B0%E5%AF%BC%E5%85%A5"
                    )
                    return False

        self.is_annotated = "response" in col_names
        return True


# 有排序对话
class QianfanSortedConversation(QianfanSchema):
    """validator for sorted, conversational dataset"""

    @_data_format_converter
    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        if table.row_number() == 0:
            log_error("no data in table")
            return False

        col_names = table.col_names()

        # 本地单轮对话带排序对接千帆的校验规则
        if "prompt" not in col_names:
            log_error("no prompt column in dataset column")
            return False
        if table.inner_table.column("prompt").null_count:
            log_error("prompt column has empty data in dataset column")
            return False

        if "response" in col_names:
            if table.inner_table.column("response").null_count:
                log_error("response column has empty data in dataset column")
                return False
            response_list = table.col_list("response")["response"]
            for index in range(len(response_list)):
                response_record = response_list[index]
                if not (isinstance(response_record, list) and len(response_record) > 0):
                    log_error(
                        f"response records illegal in dataset row {index}. response"
                        f" data: {response_record}"
                    )
                    return False
                for single_response_record in response_record:
                    if not (
                        isinstance(single_response_record, list)
                        and len(single_response_record) == 1
                        and isinstance(single_response_record[0], str)
                        and single_response_record[0]
                    ):
                        log_error(
                            f"response illegal in dataset row {index}. response data:"
                            f" {response_record}"
                            "for accurate dataset format, please check"
                            "https://cloud.baidu.com/doc/WENXINWORKSHOP/s/yliu6bqzw"
                            "#%E6%9C%89%E6%A0%87%E6%B3%A8%E4%BF%A1%E6%81%AF"
                            "-%E6%9C%AC%E5%9C%B0%E5%AF%BC%E5%85%A5"
                        )
                        return False

        self.is_annotated = "response" in col_names
        return True


# 泛文本对话
class QianfanGenericText(QianfanSchema):
    """validator for generic text dataset"""

    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        if table.row_number() == 0:
            log_error("no data in table")
            return False

        col_names = table.col_names()
        if len(col_names) != 1:
            log_error(f"dataset has more than 1 column: {col_names}")
            return False

        if table.inner_table.column(col_names[0]).null_count:
            log_error("empty row in dataset")
            return False

        return True


# 问答集
class QianfanQuerySet(QianfanSchema):
    """validator for query set dataset"""

    @_data_format_converter
    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        if table.row_number() == 0:
            log_error("no data in table")
            return False

        col_names = table.col_names()

        if "prompt" not in col_names:
            log_error("no prompt column in dataset column")
            return False
        if table.inner_table.column("prompt").null_count:
            log_error("prompt column has empty data in dataset column")
            return False

        return True


# 文生图
class QianfanText2Image(QianfanSchema):
    """validator for text to image dataset"""

    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        return False


class EvaluationSchema(Schema):
    """validator for evaluation used"""

    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        if len(table) == 0:
            log_error("table is empty")
            return False

        col_names = table.col_names()

        for column in [OldReferenceColumnName, LLMOutputColumnName]:
            if column not in col_names:
                log_error(f"{column} not in dataset columns")
                return False

        if (
            NewInputPromptColumnName in col_names
            and NewInputChatColumnName in col_names
        ):
            log_error(
                f"can't have both {NewInputChatColumnName} and"
                f" {NewInputPromptColumnName} simultaneously"
            )
            return False

        if NewInputPromptColumnName in col_names:
            elem_type = table[0][NewInputPromptColumnName]
            if not isinstance(elem_type, str):
                log_error(
                    f"element in column {NewInputPromptColumnName} isn't str, rather"
                    f" {type(elem_type)}"
                )
                return False
            return True

        if NewInputChatColumnName in col_names:
            elem_type = table[0][NewInputChatColumnName]
            if not isinstance(elem_type, str):
                log_error(
                    f"element in column {NewInputChatColumnName} isn't str, rather"
                    f" {type(elem_type)}"
                )
                return False
            return True

        log_error(
            f"no neither {NewInputChatColumnName} or {NewInputPromptColumnName} found"
        )
        return False
