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
from typing import Any, List


class Space(object):
    """
    Base class for all search spaces.
    """

    pass


class Categorical(Space):
    """
    Search space representing categorical classification types.
    """

    def __init__(self, choices: List[Any]) -> None:
        """
        Args:
          choices (List[Any]): A list of options from which to choose.
        """
        self.choices = choices


class Uniform(Space):
    """
    Search space representing a uniform distribution of continuous values
    between a specified low and high range.
    """

    def __init__(self, low: float, high: float) -> None:
        """
        Args:
            low (float): The lower bound of the uniform distribution.
            high (float): The upper bound of the uniform distribution.
        """
        self.low = low
        self.high = high
