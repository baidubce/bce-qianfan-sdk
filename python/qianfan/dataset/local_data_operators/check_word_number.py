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
    _number_words_max_map,
    _number_words_min_map,
)
from qianfan.dataset.local_data_operators.utils import (
    SentencePieceTokenizer,
    get_words_from_document,
)


class LocalCheckWordNumberFilter(BaseLocalFilterOperator):
    """check word number"""

    def __init__(
        self,
        filter_column: str,
        sentence_piece_model_path: str,
        number_words_min_cutoff: Optional[int] = None,
        number_words_max_cutoff: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(filter_column=filter_column, **kwargs)

        if not number_words_min_cutoff:
            self.number_words_min_cutoff = _number_words_min_map.get(
                self.text_language, 10
            )
        else:
            self.number_words_min_cutoff = number_words_min_cutoff

        if not number_words_max_cutoff:
            self.number_words_max_cutoff = _number_words_max_map.get(
                self.text_language, 100000
            )
        else:
            self.number_words_max_cutoff = number_words_max_cutoff

        self.sentence_piece_model = SentencePieceTokenizer(sentence_piece_model_path)

        self.strip_characters = _default_special_characters_set

    def __str__(self) -> str:
        s = "pass_name: filter_check_number_words\n"
        kwargs = {
            "text_language": self.text_language,
            "number_words_min_cutoff": self.number_words_min_cutoff,
            "number_words_max_cutoff": self.number_words_max_cutoff,
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

        return (len(words) >= self.number_words_min_cutoff) and (
            len(words) <= self.number_words_max_cutoff
        )
