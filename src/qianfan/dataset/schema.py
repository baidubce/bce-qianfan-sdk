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

from abc import ABC, abstractmethod

from qianfan.dataset.consts import QianfanDefaultColumnNameForNestedTable
from qianfan.dataset.table import Table


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


# 无排序对话
class QianfanNonSortedConversation(Schema):
    """validator for non-sorted, conversational dataset"""

    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        if table.get_row_count() == 0:
            return False

        col_names = table.col_names()

        if (
            len(col_names) == 1
            and QianfanDefaultColumnNameForNestedTable == col_names[0]
        ):
            is_response_column_existed = False
            records = table.list()[0][col_names[0]]
            for index in range(len(records)):
                conversation = records[index]
                if "prompt" not in conversation:
                    return False
                if "response" in conversation:
                    if index == 0:
                        is_response_column_existed = True
                    elif not is_response_column_existed:
                        return False
                    response_record = conversation["response"]
                    if not (
                        isinstance(response_record, list)
                        and len(response_record) == 1
                        and isinstance(response_record[0], list)
                        and len(response_record[0]) == 1
                        and isinstance(response_record[0][0], str)
                        and response_record[0][0]
                    ):
                        return False

                elif is_response_column_existed:
                    return False

            return True

        # 本地单轮对话对接千帆的校验规则
        if "prompt" not in col_names:
            return False
        if table.inner_table.column("prompt").null_count:
            return False

        if "response" in col_names:
            if table.inner_table.column("response").null_count:
                return False
            for row in table.col_list("response")["response"]:
                response_record = row
                if not (
                    isinstance(response_record, list)
                    and len(response_record) == 1
                    and isinstance(response_record[0], list)
                    and len(response_record[0]) == 1
                    and isinstance(response_record[0][0], str)
                    and response_record[0][0]
                ):
                    return False

        return True


# 有排序对话
class QianfanSortedConversation(Schema):
    """validator for sorted, conversational dataset"""

    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        if table.get_row_count() == 0:
            return False

        col_names = table.col_names()

        # 从千帆导入的数据集的校验规则
        if (
            len(col_names) == 1
            and QianfanDefaultColumnNameForNestedTable == col_names[0]
        ):
            is_response_column_existed = False
            records = table.list()[0][col_names[0]]
            for index in range(len(records)):
                conversation = records[index]
                if "prompt" not in conversation:
                    return False
                if "response" in conversation:
                    if index == 0:
                        is_response_column_existed = True
                    elif not is_response_column_existed:
                        return False
                    response_record = conversation["response"]
                    if not (
                        isinstance(response_record, list) and len(response_record) > 0
                    ):
                        return False
                    for single_response_record in response_record:
                        if not (
                            isinstance(single_response_record, list)
                            and len(single_response_record) == 1
                            and isinstance(single_response_record[0], str)
                            and single_response_record[0]
                        ):
                            return False

                elif is_response_column_existed:
                    return False

            return True

        # 本地单轮对话带排序对接千帆的校验规则
        if "prompt" not in col_names:
            return False
        if table.inner_table.column("prompt").null_count:
            return False

        if "response" in col_names:
            if table.inner_table.column("response").null_count:
                return False
            for row in table.col_list("response")["response"]:
                response_record = row
                if not (isinstance(response_record, list) and len(response_record) > 0):
                    return False
                for single_response_record in response_record:
                    if not (
                        isinstance(single_response_record, list)
                        and len(single_response_record) == 1
                        and isinstance(single_response_record[0], str)
                        and single_response_record[0]
                    ):
                        return False

        return True


# 泛文本对话
class QianfanGenericText(Schema):
    """validator for generic text dataset"""

    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        if table.get_row_count() == 0:
            return False

        col_names = table.col_names()
        if len(col_names) != 1:
            return False
        if table.inner_table.column(col_names[0]).null_count:
            return False

        elem = table.list(0)[0][col_names[0]]
        if isinstance(elem, str):
            return False

        return True


# 问答集
class QianfanQuerySet(Schema):
    """validator for query set dataset"""

    def validate(self, table: Table) -> bool:
        """
        validate a table

        Args:
            table (Table): table need to be validated

        Returns:
            bool:whether table is valid
        """
        if table.get_row_count() == 0:
            return False

        col_names = table.col_names()
        if (
            len(col_names) == 1
            and QianfanDefaultColumnNameForNestedTable == col_names[0]
        ):
            single_entry = table.list(0)[0][0]
            if "prompt" not in single_entry:
                return False
            if not isinstance(single_entry["prompt"], str):
                return False

        if "prompt" not in col_names:
            return False
        if table.inner_table.column(col_names[0]).null_count:
            return False

        elem = table.list(0)[0]["prompt"]
        if isinstance(elem, str):
            return False

        return True


# 文生图
class QianfanText2Image(Schema):
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
