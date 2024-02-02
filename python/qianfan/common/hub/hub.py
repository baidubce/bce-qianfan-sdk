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
from typing import Any, Dict, Optional, Type

import requests

from qianfan.common.hub.interface import HubSerializable, loads
from qianfan.common.prompt.prompt import Prompt
from qianfan.config import encoding
from qianfan.errors import InvalidArgumentError, RequestError, ValidationError
from qianfan.version import VERSION as sdk_version

# a map which maps the prefix of src to the class
_hub_load_type: Dict[str, Type[HubSerializable]] = {
    "prompt": Prompt,
}


def _load_from_qianfan(src: str) -> Any:
    """
    Load the object from qianfan platform.
    """
    path_list = src.split("/")
    if len(path_list) < 2:
        raise ValidationError("The src should be in the format of <type>/<name>")
    var_type = path_list[0]
    cls = _hub_load_type.get(var_type, None)
    if cls is None:
        raise ValidationError(f"The type {var_type} is not supported.")
    return cls._hub_pull("/".join(path_list[1:]))


def load(
    src: Optional[str] = None,
    json_str: Optional[str] = None,
    path: Optional[str] = None,
    url: Optional[str] = None,
) -> Any:
    """
    Loads an object from either a JSON string, a file specified by its path, or a URL.
    ONLY ONE SOURCE SHOULD BE PROVIDED.
    When multiple sources are provided, which source will be used is undefined.

    Parameters:
      src (Optional[str]):
        A str indicating the source on qianfan platform. The str should be in the
        format of <type>/<name>.
      json_str (Optional[str]):
        A JSON-formatted string containing the serialized representation of the object,
        which is the return value of the `hub.save` method.
      path (Optional[str]):
        The path to the file from which the object should be loaded.
      url (Optional[str]):
        The URL from which the object should be loaded.

    Returns:
      Any:
        The deserialized object.

    Example:
    ```python
    # Example 1: Load from qianfan platform
    prompt = load("prompt/my_prompt")

    # Example 2: Load from a JSON string
    data = save(obj)
    loaded_object = load(json_str=data)

    # Example 3: Load from a file
    file_path = 'path/to/data.json'
    loaded_object = load(path=file_path)

    # Example 4: Load from a URL
    url = 'https://example.com/data.json'
    loaded_object = load(url=url)
    ```
    """
    if src is not None:
        return _load_from_qianfan(src)
    # get `cls_desc` from different sources
    s = json_str
    if path is not None:
        with open(path, encoding=encoding()) as f:
            s = f.read()
    if url is not None:
        try:
            s = requests.get(url).text
        except requests.RequestException as e:
            raise RequestError(f"Request the target url failed. Error detail: {str(e)}")
    # TODO: support load qianfan server
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


def save(
    obj: HubSerializable,
    to_platform: bool = False,
    path: Optional[str] = None,
    dump_args: Dict[str, Any] = {},
) -> str:
    """
    Serialize the given object and save it to different sources.

    This function takes an object (`obj`) that implements the `HubSerializable`
    interface and serializes it. The serialized data is then saved to a file specified
    by the optional `path` parameter. The serialization process can be customized
    further by providing additional arguments in the `dump_args` dictionary.

    Parameters:
      obj (HubSerializable):
        The object to be serialized.
      to_platform (bool):
        Whether to push the object to qianfan platform.
      path (Optional[str]):
        The file path where the serialized data will be saved. If not provided, the
        serialized data is not saved to a file.
      dump_args (Dict[str, Any]):
        Additional keyword arguments to customize the serialization result. These
        arguments are passed to `json.dumps` function.

    Returns:
      str:
        The serialized result.
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
        json_str = json.dumps(s, **dump_args)
    except json.JSONDecodeError:
        raise ValidationError("Hub can not serialize the provided object.")
    if path is not None:
        with open(path, "w", encoding=encoding()) as f:
            f.write(json_str)
    if to_platform is True:
        obj._hub_push()
    return json_str


def push(obj: Any) -> None:
    """
    Push the object to qianfan platform.

    Parameters:
      obj (HubSerializable):
        The object to be pushed to qianfan platform.

    Returns:
      None
    """
    save(obj, to_platform=True)
