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
    _word_repetition_length_map,
    _word_repetition_max_cutoff,
)
from qianfan.dataset.local_data_operators.utils import (
    SentencePieceTokenizer,
    get_words_from_document,
)


class LocalCheckWordRepetitionFilter(BaseLocalFilterOperator):
    """remove entry with high repetition ratio"""

    def __init__(
        self,
        filter_column: str,
        sentence_piece_model_path: str,
        word_repetition_length: Optional[int] = None,
        word_repetition_max_cutoff: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(filter_column=filter_column, **kwargs)

        if not word_repetition_length:
            self.word_repetition_length = _word_repetition_length_map.get(
                self.text_language, 5
            )
        else:
            self.word_repetition_length = word_repetition_length

        if not word_repetition_max_cutoff:
            self.word_repetition_max_cutoff = _word_repetition_max_cutoff.get(
                self.text_language, 0.3
            )
        else:
            self.word_repetition_max_cutoff = word_repetition_max_cutoff

        self.sentence_piece_model = SentencePieceTokenizer(sentence_piece_model_path)

        self.strip_characters = _default_special_characters_set

    def __str__(self) -> str:
        s = "pass_name: filter_check_word_repetition_removal\n"
        kwargs = {
            "text_language": self.text_language,
            "word_repetition_length": self.word_repetition_length,
            "word_repetition_max_cutoff": self.word_repetition_max_cutoff,
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

        def _get_freq_word_ngrams(content: str, n: int) -> Dict[str, int]:
            words = get_words_from_document(
                content,
                self.text_language,
                sentence_piece_tokenizer=self.sentence_piece_model,
                need_to_lower=False,
                strip_characters=self.strip_characters,
            )

            word_ngrams: List[str] = [
                " ".join(words[i : i + n]) for i in range(len(words) - n + 1)
            ]

            freq: Dict[str, int] = {}
            for word_ngram in word_ngrams:
                freq[word_ngram] = freq.get(word_ngram, 0) + 1
            return freq

        freq_word_ngrams = _get_freq_word_ngrams(document, self.word_repetition_length)
        if len(freq_word_ngrams) == 0:
            word_repetition_ratio = 0.0
        else:
            freq_word_ngrams_values = list(freq_word_ngrams.values())
            word_repetition_ratio = sum(
                freq for freq in freq_word_ngrams_values if freq > 1
            ) / sum(freq_word_ngrams_values)

        return word_repetition_ratio <= self.word_repetition_max_cutoff
