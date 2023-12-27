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
Hub Interface
"""

import importlib
from copy import deepcopy
from enum import Enum
from typing import Any, Dict

from qianfan.errors import ValidationError


def dumps(obj: Any) -> Any:
    """
    serialize the object to json string
    """
    if isinstance(obj, HubSerializable):
        return obj._hub_serialize()

    if isinstance(obj, Enum):
        return {
            "module": obj.__class__.__module__,
            "type": obj.__class__.__name__,
            # use `_hub_serialize` to serialize the object
            "args": {
                "value": obj.value,
            },
        }
    if isinstance(obj, list):
        return [dumps(i) for i in obj]
    # distinguish between object arguments and dict
    if isinstance(obj, dict):
        return {
            "module": "",
            "type": "dict",
            "args": {k: dumps(v) for k, v in obj.items()},
        }
    return obj


def loads(data: Any) -> Any:
    """
    deserialize the object from dict
    """
    if isinstance(data, list):
        return [loads(i) for i in data]
    if isinstance(data, dict):
        # if is normal dict
        if data.get("type", None) == "dict":
            return {k: loads(v) for k, v in data["args"].items()}
        # load the class from module
        mod = importlib.import_module(data["module"])
        cls = getattr(mod, data["type"])

        # check whether the class support hub serialization
        if issubclass(cls, HubSerializable):
            return cls._hub_deserialize({k: loads(v) for k, v in data["args"].items()})
        elif issubclass(cls, Enum):
            return cls(data["args"]["value"])
        raise ValidationError(
            f"Type `{data['type']}` is not supported to be loaded by hub."
        )

    # call deserialize method to create the object
    return data


class HubSerializable(object):
    """
    HubInterface
    """

    def _hub_serialize(self) -> Dict[str, Any]:
        """
        serialize the object to dict
        """
        dic = deepcopy(self.__dict__)
        for k, v in dic.items():
            dic[k] = dumps(v)
        return {
            "module": self.__class__.__module__,
            "type": self.__class__.__name__,
            # use `_hub_serialize` to serialize the object
            "args": dic,
        }

    @classmethod
    def _hub_deserialize(cls, data: Dict[str, Any]) -> "HubSerializable":
        """
        restore the object from dict
        """

        return cls(**data)

    @classmethod
    def _hub_pull(cls, name: str) -> "HubSerializable":
        """
        load the object from qianfan platform
        """
        raise ValidationError(f"Not supported to pull {type(cls).__name__} from hub.")

    def _hub_push(cls) -> None:
        """
        load the object from qianfan platform
        """
        raise ValidationError(f"Not supported to push {type(cls).__name__} to hub.")
