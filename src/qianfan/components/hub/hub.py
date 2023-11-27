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

import json
from typing import Any, Optional

from qianfan.components.hub.interface import HubSerializable, loads
from qianfan.errors import InvalidArgumentError, ValidationError
from qianfan.version import VERSION as sdk_version


def load(json_str: Optional[str] = None, path: Optional[str] = None) -> Any:
    """
    Load a object from different sources
    """
    # get `cls_desc` from different sources
    s = json_str
    if path is not None:
        with open(path) as f:
            s = f.read()
    # TODO: support load from url and qianfan server
    if s is None:
        raise InvalidArgumentError("No content provided to load the object.")
    try:
        cls_desc = json.loads(s)
    except json.JSONDecodeError:
        raise InvalidArgumentError(
            "Hub can not decode the provided content. Please check the content."
        )

    # call deserialize method to create the object
    return loads(cls_desc["obj"])


def save(obj: HubSerializable, path: Optional[str] = None) -> str:
    """
    Save the object to different sources
    """
    if not isinstance(obj, HubSerializable):
        raise ValidationError(
            f"The type `{obj.__class__.__name__}` does not support being saved by hub."
        )
    s = {
        "sdk_version": sdk_version,
        # use `_hub_serialize` to serialize the object
        "obj": obj._hub_serialize(),
    }
    try:
        json_str = json.dumps(s)
    except json.JSONDecodeError:
        raise ValidationError("Hub can not serialize the provided object.")
    if path is not None:
        with open(path, "w") as f:
            f.write(json_str)
    return json_str
