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

import math
from typing import Optional, Dict, Any

from qianfan.utils.pydantic import Field, root_validator

from qianfan.dataset.local_data_operators.local_data_operator_consts import _character_repetition_length_map, \
    _character_repetition_max_cutoff_map
from qianfan.dataset.local_data_operators.base_local_data_operator import BaseLocalFilterOperator


class LocalCheckCharacterRepetitionFilter(BaseLocalFilterOperator):
    """remove entry with high repetition ratio"""

    character_repetition_length: Optional[int] = Field(default=None)
    character_repetition_max_cutoff: Optional[int] = Field(default=None)

    @root_validator()
    @classmethod
    def _fill_param(cls, input_dicts: Dict[str, Any]) -> Dict[str, Any]:
        if not input_dicts["character_repetition_length"]:
            input_dicts["character_repetition_length"] = _character_repetition_length_map.get(
                input_dicts["text_language"], 10)

        if not input_dicts["character_repetition_max_cutoff"]:
            input_dicts["character_repetition_max_cutoff"] = _character_repetition_max_cutoff_map.get(
                input_dicts["text_language"], 0.2)

        return input_dicts

    def __str__(self) -> str:
        s = 'filter_name: filter_check_character_repetition_removal'
        kwargs = {
            'lang_dataset_id': self.lang_dataset_id,
            'character_repetition_length': self.character_repetition_length,
            'character_repetition_max_cutoff':
                self.character_repetition_max_cutoff
        }
        for k, v in kwargs.items():
            s += f'\t\t{k}: {v}\n'
        return s

    def __call__(self, entry: Dict[str, Any], *args, **kwargs) -> bool:
        document = entry[self.filter_column]

        def get_freq_character_ngrams(content: str, n: int) -> Dict[str, int]:
            character_ngrams = [
                content[i:i + n] for i in range(len(content) - n + 1)
            ]
            frequency_ngrams: Dict[str, int] = {}
            for character_ngram in character_ngrams:
                frequency_ngrams[character_ngram] = frequency_ngrams.get(character_ngram, 0) + 1
            return frequency_ngrams

        freq_character_ngrams = get_freq_character_ngrams(document, self.character_repetition_length)
        if len(freq_character_ngrams) == 0:
            character_repetition_ratio = 0.0
        else:
            freq_character_ngrams = list(freq_character_ngrams.values())
            freq_character_ngrams = sorted(freq_character_ngrams, reverse=True)
            val_one = len([el for el in freq_character_ngrams if el == 1])
            num_rep_character_ngrams = min(
                int(math.sqrt(len(freq_character_ngrams))),
                len(freq_character_ngrams) - val_one,
            )
            character_repetition_ratio = sum(
                freq_character_ngrams[:num_rep_character_ngrams]) / sum(
                freq_character_ngrams)

        return character_repetition_ratio <= self.character_repetition_max_cutoff
