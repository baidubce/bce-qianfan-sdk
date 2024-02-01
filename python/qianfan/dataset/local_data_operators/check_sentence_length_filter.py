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

from typing import Any, Dict, List, Union

from qianfan.dataset.local_data_operators.base import (
    BaseLocalFilterOperator,
)
from qianfan.dataset.local_data_operators.utils import (
    pyltp_split_sentence,
)


class LocalCheckEachSentenceIsLongEnoughFilter(BaseLocalFilterOperator):
    """check sentence length"""

    def __init__(
        self,
        filter_column: str,
        short_sentence_ratio_max_cutoff: float = 0.6,
        short_sentence_max_cutoff: int = 5,
        **kwargs: Any,
    ) -> None:
        self.short_sentence_ratio_max_cutoff = short_sentence_ratio_max_cutoff
        self.short_sentence_max_cutoff = short_sentence_max_cutoff
        super().__init__(filter_column=filter_column, **kwargs)

    def __str__(self) -> str:
        s = "filter_name: filter_check_each_sentence_is_long_enough\n"
        kwargs = {
            "text_language": self.text_language,
            "short_sentence_ratio_max_cutoff": self.short_sentence_ratio_max_cutoff,
            "short_sentence_max_cutoff": self.short_sentence_max_cutoff,
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
        sentences = pyltp_split_sentence(document)
        if len(sentences) == 0:
            return False

        cond = True
        hit = 0

        for sent in sentences:
            if len(sent) <= self.short_sentence_max_cutoff:
                hit += 1
        short_sentence_ratio = hit / len(sentences)
        if short_sentence_ratio > self.short_sentence_ratio_max_cutoff:
            cond = False

        return cond
