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
from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Generic,
    Optional,
    TypeVar,
)

Input = TypeVar("Input")
Output = TypeVar("Output")


class Executable(Generic[Input, Output], ABC):
    """
    generic abstraction class of executable

    """

    @abstractmethod
    def exec(self, input: Optional[Input] = None, **kwargs: Dict) -> Output:
        ...


class Serializable(ABC):
    """
    generic abstraction class of serializable.
    especially for the model, service, and trainer.
    """

    @abstractmethod
    def dumps(self) -> Optional[bytes]:
        """
        dumps

        Returns:
            serialized bytes data
        """
        ...

    @abstractmethod
    def loads(self, data: bytes) -> Any:
        """
        loads

        Parameters:
            data (bytes): load

        Returns:
            Any: _description_
        """
        ...


class ExecuteSerializable(Executable[Input, Output], Serializable):
    """
    set of executable and serializable. subclass implement it to support
    exec and dumps/loads.
    """

    ...
