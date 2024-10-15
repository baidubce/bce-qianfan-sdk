# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
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
"""data insight"""

import math
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Union

from pydantic import BaseModel, Field

from qianfan.dataset import Dataset
from qianfan.dataset.data_insight.data_insight_utils import (
    _get_generator,
)
from qianfan.dataset.local_data_operators.consts import _default_special_characters_set
from qianfan.dataset.local_data_operators.utils import (
    SentencePieceTokenizer,
    get_augmentation_word_list,
    get_words_from_document,
)
from qianfan.dataset.local_data_operators.word_list import _flagged_words


def get_content_length_for_each_entry(
    entry: Union[List[Dict[str, Any]], Dict[str, Any], str],
    column: Optional[str] = None,
    **kwargs: Any,
) -> Union[Generator, Dict[str, Any]]:
    length_column_name = "content_length"

    if isinstance(entry, str):
        return {length_column_name: len(entry)}

    assert column is not None
    if isinstance(entry, list):

        def _generator(
            entry: List[Dict[str, Any]]
        ) -> Generator[Dict[str, Any], None, None]:
            for elem in entry:
                yield {length_column_name: len(elem[column])}

        return _generator(entry)

    elif isinstance(entry, dict):
        return {length_column_name: len(entry[column])}
    else:
        raise ValueError(f"unexpected entry type: {type(entry)}")


def get_character_repetition_ratio(
    entry: Union[List[Dict[str, Any]], Dict[str, Any], str],
    column: Optional[str] = None,
    character_repetition_length: int = 10,
    **kwargs: Any,
) -> Union[Generator, Dict[str, Any]]:
    def _calculate_single(single: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        if isinstance(single, str):
            document = single
        else:
            assert column
            document = single[column]

        def _get_freq_character_ngrams(content: str, n: int) -> Dict[str, int]:
            character_ngrams = [content[i : i + n] for i in range(len(content) - n + 1)]
            frequency_ngrams: Dict[str, int] = {}
            for character_ngram in character_ngrams:
                frequency_ngrams[character_ngram] = (
                    frequency_ngrams.get(character_ngram, 0) + 1
                )
            return frequency_ngrams

        freq_character_ngrams = _get_freq_character_ngrams(
            document, character_repetition_length
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

        return {"character_repetition_ratio": character_repetition_ratio}

    if isinstance(entry, list):
        return _get_generator(entry, _calculate_single)
    else:
        return _calculate_single(entry)


def get_special_characters_ratio(
    entry: Union[List[Dict[str, Any]], Dict[str, Any], str],
    column: Optional[str] = None,
    special_character_set: Set[str] = _default_special_characters_set,
    **kwargs: Any,
) -> Union[Generator, Dict[str, Any]]:
    def _calculate_single(single: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        if isinstance(single, str):
            document = single
        else:
            assert column
            document = single[column]

        if len(document) == 0:
            special_characters_ratio = 0.0
        else:
            special_characters_ratio = len(
                [char for char in document if char in special_character_set]
            ) / len(document)

        return {"special_characters_ratio": special_characters_ratio}

    if isinstance(entry, list):
        return _get_generator(entry, _calculate_single)
    else:
        return _calculate_single(entry)


def get_flagged_word_ratio(
    entry: Union[List[Dict[str, Any]], Dict[str, Any], str],
    sentence_piece_model_path: str,
    column: Optional[str] = None,
    words_augmentation_group_sizes: List[int] = [2],
    stripped_charset: Set[str] = _default_special_characters_set,
    flagged_set: Set[str] = set(_flagged_words.get("zh", [])),
    **kwargs: Any,
) -> Union[Generator, Dict[str, Any]]:
    sentence_piece_model = SentencePieceTokenizer(sentence_piece_model_path)

    def _calculate_single(single: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        if isinstance(single, str):
            document = single
        else:
            assert column
            document = single[column]

        words = get_words_from_document(
            document,
            "ZH",
            sentence_piece_tokenizer=sentence_piece_model,
            need_to_lower=False,
            strip_characters=stripped_charset,
        )

        if not words:
            flagged_words_ratio = 0.0
        else:
            augmentation: List[str] = []
            if len(words_augmentation_group_sizes) > 0:
                augmentation = get_augmentation_word_list(
                    words,
                    words_augmentation_group_sizes,
                    "",
                )

            flagged_words_ratio = len(
                [word for word in words + augmentation if word in flagged_set]
            ) / len(words)

        if flagged_words_ratio > 1.0:
            flagged_words_ratio = 1.0

        return {"flagged_words_ratio": flagged_words_ratio}

    if isinstance(entry, list):
        return _get_generator(entry, _calculate_single)
    else:
        return _calculate_single(entry)


class DatasetInsight(BaseModel):
    operator_list: List[
        Callable[
            [Union[List[Dict[str, Any]], Dict[str, Any], str]],
            Union[Generator, Dict[str, Any]],
        ]
    ] = Field(
        default=[
            get_content_length_for_each_entry,
            get_character_repetition_ratio,
            get_special_characters_ratio,
        ]
    )

    def insight(
        self, ds: Dataset, column: Optional[str] = None, **kwargs: Any
    ) -> Dataset:
        def _closure(
            entry: Union[List[Dict[str, Any]], Dict[str, Any], str]
        ) -> Union[Generator, Dict[str, Any]]:
            result_list: List = [
                operator(entry, column=column, **kwargs)  # type: ignore
                for operator in self.operator_list
            ]

            # 需要兼容，因为这里有可能是返回迭代器（针对 List 的情况）
            if isinstance(result_list[0], Generator):
                # 这里返回一个生成器函数而不是直接 Yield 的原因是
                # 防止 Python 解释器将整个外围函数当成生成器

                assert isinstance(entry, list)
                assert column is not None

                def _generator() -> Generator:
                    index = 0
                    while True:
                        return_dict: Dict[str, Any] = {}
                        for generator in result_list:
                            return_dict.update(next(generator))

                        return_dict[column] = entry[index][column]
                        index += 1

                        yield return_dict

                return _generator()
            else:
                return_dict: Dict[str, Any] = {}
                for result in result_list:
                    return_dict.update(result)

                column_name = column if column else "content"
                column_value = (
                    entry[column] if column and isinstance(entry, dict) else entry
                )
                return_dict[column_name] = column_value

                return return_dict

        return ds.map(_closure, should_create_new_obj=True)
