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

from datetime import datetime
from typing import Any, Optional, Type, TypeVar

from rich import print

from qianfan.resources.llm.base import BaseResource

BaseResourceType = TypeVar("BaseResourceType", bound=BaseResource)


def print_error_msg(msg: str) -> None:
    """
    Print an error message in the console.
    """
    print(f"[bold red]ERROR[/bold red]: {msg}")


def print_warn_msg(msg: str) -> None:
    """
    Print a warning message in the console.
    """
    print(f"[bold orange1]WARN[/bold orange1]: {msg}")


def create_client(
    type: Type[BaseResourceType], model: str, endpoint: Optional[str], **kwargs: Any
) -> BaseResourceType:
    """
    Create the client according to the type, model and endpoint.
    """
    if endpoint is not None:
        return type(endpoint=endpoint, **kwargs)
    else:
        return type(model=model, **kwargs)


def timestamp(time: datetime = datetime.now()) -> str:
    """
    Return a timestamp string used in the client.
    """
    return time.strftime("%Y%m%d_%H%M%S")
