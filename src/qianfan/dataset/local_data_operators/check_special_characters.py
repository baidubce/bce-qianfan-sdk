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
data operator for local using
"""

from typing import Any, Dict, List, Optional, Set, Union

from qianfan.dataset.local_data_operators.base import (
    BaseLocalFilterOperator,
)
from qianfan.dataset.local_data_operators.consts import (
    _default_special_characters_set,
    _special_character_map,
)


class LocalCheckSpecialCharactersFilter(BaseLocalFilterOperator):
    """check special characters"""

    def __init__(
        self,
        filter_column: str,
        special_characters: Set = _default_special_characters_set,
        special_characters_max_cutoff: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(filter_column=filter_column, **kwargs)
        self.special_characters = special_characters

        if not special_characters_max_cutoff:
            self.special_characters_max_cutoff = _special_character_map.get(
                self.text_language, 0.40
            )
        else:
            self.special_characters_max_cutoff = special_characters_max_cutoff

    def __str__(self) -> str:
        s = "pass_name: filter_check_special_characters\n"
        kwargs = {
            "text_language": self.text_language,
            "special_characters_max_cutoff": self.special_characters_max_cutoff,
        }
        for k, v in kwargs.items():
            s += f"\t\t{k}: {v}\n"
        return s

    def __call__(
        self,
        entry: Union[Dict[str, Any], List[Dict[str, Any]], str],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        document = self._get_real_document_from_entry(entry)

        if len(document) == 0:
            special_characters_ratio = 0.0
        else:
            special_characters_ratio = len(
                [char for char in document if char in self.special_characters]
            ) / len(document)
        return special_characters_ratio <= self.special_characters_max_cutoff
