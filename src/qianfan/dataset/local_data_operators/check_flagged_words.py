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
from typing import Any, Dict, List, Optional, Union

from qianfan.dataset.local_data_operators.base import (
    BaseLocalFilterOperator,
)
from qianfan.dataset.local_data_operators.consts import (
    _default_special_characters_set,
    _flagged_words_max_cutoff_map,
    _words_augmentation_group_sizes_map,
    _words_augmentation_join_char_map,
)
from qianfan.dataset.local_data_operators.utils import (
    SentencePieceTokenizer,
    get_augmentation_word_list,
    get_words_from_document,
)
from qianfan.dataset.local_data_operators.word_list import _flagged_words


class LocalCheckFlaggedWordsFilter(BaseLocalFilterOperator):
    """check flagged words"""

    def __init__(
        self,
        filter_column: str,
        sentence_piece_model_path: str,
        words_augmentation_group_sizes: Optional[List[int]] = None,
        words_augmentation_join_char: Optional[str] = None,
        flagged_words_max_cutoff: Optional[float] = None,
        **kwargs: Any,
    ):
        super().__init__(filter_column=filter_column, **kwargs)

        if not words_augmentation_group_sizes:
            self.words_augmentation_group_sizes = (
                _words_augmentation_group_sizes_map.get(self.text_language, [])
            )
        else:
            self.words_augmentation_group_sizes = words_augmentation_group_sizes

        if not words_augmentation_join_char:
            self.words_augmentation_join_char = _words_augmentation_join_char_map.get(
                self.text_language, ""
            )
        else:
            self.words_augmentation_join_char = words_augmentation_join_char

        if not flagged_words_max_cutoff:
            self.flagged_words_max_cutoff = _flagged_words_max_cutoff_map.get(
                self.text_language, 0.1
            )
        else:
            self.flagged_words_max_cutoff = flagged_words_max_cutoff

        self.flagged_words_set = set(_flagged_words.get(self.text_language.lower(), []))

        self.sentence_piece_model = SentencePieceTokenizer(sentence_piece_model_path)

        self.strip_characters = _default_special_characters_set

    def __str__(self) -> str:
        s = "pass_name: filter_check_flagged_words\n"
        kwargs = {
            "text_language": self.text_language,
            "words_augmentation_group_sizes": self.words_augmentation_group_sizes,
            "words_augmentation_join_char": self.words_augmentation_join_char,
            "flagged_words_max_cutoff": self.flagged_words_max_cutoff,
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

        words = get_words_from_document(
            document,
            self.text_language,
            sentence_piece_tokenizer=self.sentence_piece_model,
            need_to_lower=False,
            strip_characters=self.strip_characters,
        )

        if not words:
            flagged_words_ratio = 0.0
        else:
            augmentation: List[str] = []
            if len(self.words_augmentation_group_sizes) > 0:
                augmentation = get_augmentation_word_list(
                    words,
                    self.words_augmentation_group_sizes,
                    self.words_augmentation_join_char,
                )

            flagged_words_ratio = len(
                [
                    word
                    for word in words + augmentation
                    if word in self.flagged_words_set
                ]
            ) / len(words)

        if flagged_words_ratio > 1.0:
            flagged_words_ratio = 1.0

        return flagged_words_ratio <= self.flagged_words_max_cutoff
