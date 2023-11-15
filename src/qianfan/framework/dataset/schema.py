from abc import ABC, abstractmethod

import pyarrow.compute

from qianfan.framework.dataset.table import Table


class Schema(ABC):
    @abstractmethod
    def validate(self, table: Table) -> bool:
        """
        将 table 对象传入，然后做校验。
        目前只校验数据集字段格式，不校验内容缺失问题。
        """


# 无排序对话
class QianfanNonSortedConversation(Schema):
    def validate(self, table: Table) -> bool:
        if table.get_row_count() == 0:
            return False

        col_names = table.col_names()
        if "prompt" not in col_names:
            return False

        if "response" in col_names:
            if table.inner_table.column("response").null_count:
                return False
            response_record = table.list(0)[0]["response"]
            if not (
                isinstance(response_record, list)
                and len(response_record) == 1
                and isinstance(response_record[0], str)
            ):
                return False

        return True


# 有排序对话
class QianfanSortedConversation(Schema):
    def validate(self, table: Table) -> bool:
        if table.get_row_count() == 0:
            return False

        col_names = table.col_names()
        if "prompt" not in col_names:
            return False

        if "response" in col_names:
            if table.inner_table.column("response").null_count:
                return False
            response_record = table.list(0)[0]["response"]
            if not (
                isinstance(response_record, list)
                and isinstance(response_record[0], str)
            ):
                return False

        return True


# 泛文本对话
class QianfanGenericText(Schema):
    def validate(self, table: Table) -> bool:
        if table.get_row_count() == 0:
            return False

        col_names = table.col_names()
        if len(col_names) != 1:
            return False

        elem = table.list(0)[0][col_names[0]]
        if isinstance(elem, str):
            return False

        return True


# 问答集
class QianfanQuerySet(Schema):
    def validate(self, table: Table) -> bool:
        if table.get_row_count() == 0:
            return False

        col_names = table.col_names()
        if "prompt" not in col_names:
            return False

        elem = table.list(0)[0]["prompt"]
        if isinstance(elem, str):
            return False

        return True


# 文生图
class QianfanText2Image(Schema):
    def validate(self, table: Table) -> bool:
        return False
