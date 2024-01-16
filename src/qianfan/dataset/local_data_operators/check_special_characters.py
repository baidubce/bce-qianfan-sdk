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

from typing import Dict, Any, Optional, Set

from qianfan.dataset.local_data_operators.base_local_data_operator import BaseLocalFilterOperator
from qianfan.dataset.local_data_operators.local_data_operator_consts import default_special_characters_set, \
    _special_character_map
from qianfan.utils.pydantic import Field, root_validator


class LocalCheckSpecialCharactersFilter(BaseLocalFilterOperator):
    """check special characters"""

    special_characters: Optional[Set] = Field(default=None)
    special_characters_max_cutoff: Optional[float] = Field(default=None)

    @root_validator(pre=True)
    @classmethod
    def _fill_param(cls, input_dicts: Dict[str, Any]) -> Dict[str, Any]:
        if not input_dicts["special_characters"]:
            input_dicts["special_characters"] = default_special_characters_set

        if not input_dicts["special_characters_max_cutoff"]:
            input_dicts["special_characters_max_cutoff"] = _special_character_map.get(
                input_dicts["text_language"], 0.40
            )

        return input_dicts

    def __str__(self) -> str:
        s = 'pass_name: filter_check_special_characters\n'
        kwargs = {
            'lang_dataset_id': self.lang_dataset_id,
            'special_characters_max_cutoff': self.special_characters_max_cutoff
        }
        for k, v in kwargs.items():
            s += f'\t\t{k}: {v}\n'
        return s

    def __call__(self, entry: Dict[str, Any], *args, **kwargs) -> bool:
        document = entry[self.filter_column]

        if len(document) == 0:
            special_characters_ratio = 0.0
        else:
            special_characters_ratio = len([
                char for char in document if char in self.special_characters
            ]) / len(document)
        return special_characters_ratio <= self.special_characters_max_cutoff
