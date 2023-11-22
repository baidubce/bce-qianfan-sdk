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
Hub
"""

import importlib
import json
from typing import Any, Optional

import qianfan
from qianfan.components.hub.interface import HubSerializable
from qianfan.resources.typing import InvalidArgumentError


def load(s: str, path: Optional[str] = None) -> Any:
    # 先从不同源获取到目标的描述 cls_desc，即上述的格式
    if path is not None:
        with open(path) as f:
            cls_desc = json.load(f)
    cls_desc = json.loads(s)
    # 然后根据 type 动态寻找目标类
    mod = importlib.import_module(cls_desc["module"])
    cls = getattr(mod, cls_desc["type"])

    # 可以设置个基类用于表示是否可以支持通过这一方式加载
    if not issubclass(cls, HubSerializable):
        raise InvalidArgumentError(f"type {cls_desc['type']} is not supported")

    # 最后调用构造函数即可完成对象的创建
    return cls._hub_deserialize(cls_desc["args"])


def save(obj: HubSerializable, path: Optional[str] = None) -> str:
    if not isinstance(obj, HubSerializable):
        raise InvalidArgumentError(
            f"the type `{obj.__class__.__name__}` does not support being saved by hub."
        )
    s = {
        "module": obj.__class__.__module__,
        "type": obj.__class__.__name__,
        "sdk_version": qianfan.__version__,
        "args": obj._hub_serialize(),
    }
    return json.dumps(s)
