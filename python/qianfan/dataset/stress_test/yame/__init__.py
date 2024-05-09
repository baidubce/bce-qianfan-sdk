"""
locust runner lib
"""
from typing import Any, Dict


class GlobalData:
    """global data which locustfile can read"""

    data: Dict[str, Any] = {}
