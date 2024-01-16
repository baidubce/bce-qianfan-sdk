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
from typing import Any, Dict, List, Optional, Set

from qianfan.dataset.local_data_operators.base_local_data_operator import (
    BaseLocalFilterOperator,
)
from qianfan.dataset.local_data_operators.local_data_operator_consts import (
    _flagged_words_max_cutoff_map,
    _words_augmentation_group_sizes_map,
    _words_augmentation_join_char_map,
    default_special_characters_set,
)
from qianfan.dataset.local_data_operators.local_operator_utils import (
    get_words_from_document,
    words_augmentation,
)
from qianfan.dataset.local_data_operators.word_list import flagged_words
from qianfan.utils.pydantic import Field, root_validator


class LocalCheckFlaggedWordsFilter(BaseLocalFilterOperator):
    strip_characters: Set[str] = default_special_characters_set
    sentence_piece_model_path: str
    words_augmentation_group_sizes: Optional[List[int]] = Field(default=None)
    words_augmentation_join_char: Optional[str] = Field(default=None)
    flagged_words_max_cutoff: Optional[float] = Field(default=None)
    flagged_words_set: Optional[Set[str]] = Field(default=None)

    @root_validator
    @classmethod
    def _fill_param(cls, input_dicts: Dict[str, Any]) -> Dict[str, Any]:
        if not input_dicts["words_augmentation_group_sizes"]:
            input_dicts["words_augmentation_group_sizes"] = (
                _words_augmentation_group_sizes_map.get(
                    input_dicts["text_language"], []
                )
            )

        if not input_dicts["words_augmentation_join_char"]:
            input_dicts["words_augmentation_join_char"] = (
                _words_augmentation_join_char_map.get(input_dicts["text_language"], "")
            )

        if not input_dicts["flagged_words_max_cutoff"]:
            input_dicts["flagged_words_max_cutoff"] = _flagged_words_max_cutoff_map.get(
                input_dicts["text_language"], 0.1
            )

        input_dicts["flagged_words_set"] = set(
            flagged_words.get(str.lower(input_dicts["text_language"]), [])
        )

        return input_dicts

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

    def __call__(self, entry: Dict[str, Any], *args: Any, **kwargs: Any) -> bool:
        document = entry[self.filter_column]

        if self.text_language not in ["ZH"]:
            # 不是中文的话，才用空格\t等标记进行分词
            sentence_piece_tokenizer = None
        else:
            # 只有中文才会使用sentence_piece_tokenizer进行分词
            sentence_piece_tokenizer = self.sentence_piece_tokenizer

        words = get_words_from_document(
            document,
            sentence_piece_tokenizer=sentence_piece_tokenizer,
            need_to_lower=False,
            strip_characters=self.strip_characters,
        )

        if not words:
            flagged_words_ratio = 0.0
        else:
            augmentation = []

            assert self.words_augmentation_group_sizes
            assert self.words_augmentation_join_char
            if len(self.words_augmentation_group_sizes) > 0:
                augmentation = [
                    words_augmentation(
                        words, group_size, self.words_augmentation_join_char
                    )
                    for group_size in self.words_augmentation_group_sizes
                ]
                augmentation = [word for augm in augmentation for word in augm]

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
