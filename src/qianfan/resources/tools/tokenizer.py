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
Tokenizer
"""

import unicodedata
from typing import Any

from qianfan.errors import InternalError, InvalidArgumentError


class Tokenizer(object):
    """
    Class for Tokenizer API
    """

    @classmethod
    def count_tokens(
        cls, text: str, mode: str = "local", model: str = "ERNIE-Bot", **kwargs: Any
    ) -> int:
        """
        Count the number of tokens in a given text.

        Parameters:
          text (str):
            The input text for which tokens need to be counted.
          mode (str, optional):
            `local` (default):
              local **SIMULATION** (Chinese characters count + English word count * 1.3)
          model (str, optional):
            The name of the model to be used for token counting, which
            may influence the counting strategy. Default is 'ERNIE-Bot'.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        """
        if mode not in ["local"]:
            raise InvalidArgumentError(
                f"Mode `{mode}` is not supported for count token, supported mode:"
                " `local`"
            )
        if mode == "local":
            return cls._local_count_tokens(text)

        # unreachable
        raise InternalError

    @classmethod
    def _local_count_tokens(cls, text: str, model: str = "ERNIE-Bot") -> int:
        """
        Calculate the token count for a given text using a local simulation.

        ** THIS IS CALCULATED BY LOCAL SIMULATION, NOT REAL TOKEN COUNT **

        The token count is computed as follows:
        (Chinese characters count) + (English word count * 1.3)
        """
        han_count = 0
        text_only_word = ""
        for ch in text:
            if cls._is_cjk_character(ch):
                han_count += 1
                text_only_word += " "
            elif cls._is_punctuation(ch) or cls._is_space(ch):
                text_only_word += " "
            else:
                text_only_word += ch
        word_count = len(list(filter(lambda x: x != "", text_only_word.split(" "))))
        return han_count + int(word_count * 1.3)

    @staticmethod
    def _is_cjk_character(ch: str) -> bool:
        """
        Check if the character is CJK character.
        """
        code = ord(ch)
        return 0x4E00 <= code <= 0x9FFF

    @staticmethod
    def _is_space(ch: str) -> bool:
        """
        Check if the character is space.
        """
        return ch in {" ", "\n", "\r", "\t"} or unicodedata.category(ch) == "Zs"

    @staticmethod
    def _is_punctuation(ch: str) -> bool:
        """
        Check if the character is punctuation.
        """
        code = ord(ch)
        return (
            33 <= code <= 47
            or 58 <= code <= 64
            or 91 <= code <= 96
            or 123 <= code <= 126
            or unicodedata.category(ch).startswith("P")
        )
