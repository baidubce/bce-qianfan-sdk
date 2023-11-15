from typing import Any, Dict


class QianfanOperator:
    operator_name: str
    arg_dict: Dict[str, Any]


class ExceptionRegulator(QianfanOperator):
    pass


class Filter(QianfanOperator):
    pass


class Deduplicator(QianfanOperator):
    pass


class SensitiveDataProcessor(QianfanOperator):
    pass
