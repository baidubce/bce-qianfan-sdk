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
from typing import Any, Dict, List, Optional, Union

from qianfan.dataset.local_data_operators.base import (
    BaseLocalFilterOperator,
)
from qianfan.dataset.local_data_operators.consts import (
    _character_repetition_length_map,
    _character_repetition_max_cutoff_map,
)


class LocalCheckCharacterRepetitionFilter(BaseLocalFilterOperator):
    """remove entry with high repetition ratio"""

    def __init__(
        self,
        filter_column: str,
        character_repetition_length: Optional[int] = None,
        character_repetition_max_cutoff: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(filter_column=filter_column, **kwargs)

        if not character_repetition_length:
            self.character_repetition_length = _character_repetition_length_map.get(
                self.text_language, 10
            )
        else:
            self.character_repetition_length = character_repetition_length

        if not character_repetition_max_cutoff:
            self.character_repetition_max_cutoff = (
                _character_repetition_max_cutoff_map.get(self.text_language, 0.2)
            )
        else:
            self.character_repetition_max_cutoff = character_repetition_max_cutoff

    def __str__(self) -> str:
        s = "filter_name: filter_check_character_repetition_removal"
        kwargs = {
            "text_language": self.text_language,
            "character_repetition_length": self.character_repetition_length,
            "character_repetition_max_cutoff": self.character_repetition_max_cutoff,
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

        def _get_freq_character_ngrams(content: str, n: int) -> Dict[str, int]:
            character_ngrams = [content[i : i + n] for i in range(len(content) - n + 1)]
            frequency_ngrams: Dict[str, int] = {}
            for character_ngram in character_ngrams:
                frequency_ngrams[character_ngram] = (
                    frequency_ngrams.get(character_ngram, 0) + 1
                )
            return frequency_ngrams

        freq_character_ngrams = _get_freq_character_ngrams(
            document, self.character_repetition_length
        )

        if len(freq_character_ngrams) == 0:
            character_repetition_ratio = 0.0
        else:
            freq_character_ngram_values = list(freq_character_ngrams.values())
            freq_character_ngram_values = sorted(
                freq_character_ngram_values, reverse=True
            )

            val_one = len([el for el in freq_character_ngram_values if el == 1])
            num_rep_character_ngrams = min(
                int(math.sqrt(len(freq_character_ngram_values))),
                len(freq_character_ngram_values) - val_one,
            )
            character_repetition_ratio = sum(
                freq_character_ngram_values[:num_rep_character_ngrams]
            ) / sum(freq_character_ngram_values)

        return character_repetition_ratio <= self.character_repetition_max_cutoff
