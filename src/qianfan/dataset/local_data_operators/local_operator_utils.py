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
utilities for local data operators
"""
import re
from typing import List, Set, Union

import sentencepiece
from ltp import StnSplit

from qianfan.utils import log_warn

spliter = StnSplit()


def pyltp_split_sentence(document: str) -> List[str]:
    """use ltp to split sentence"""

    global spliter
    try:
        sentences = spliter.split(document)  # split sentences
    except Exception as e:
        err_msg = (
            f"error occurred during split document into sentence: {str(e)}, make"
            " sentences list empty"
        )
        log_warn(err_msg)
        sentences = []
    return sentences


class SentencePieceTokenizer(object):
    """sentencepiece package tokenizer"""

    def __init__(self, sentencepiece_model_path: str) -> None:
        self.sentencepiece_model_path: str = sentencepiece_model_path
        self.sentencepiece_model = sentencepiece.SentencePieceProcessor()
        self.sentencepiece_model.Load(sentencepiece_model_path)

    def tokenize(
        self, document: str, join_on_whitespace: bool = False
    ) -> Union[str, List[str]]:
        document_tokenized = self.sentencepiece_model.EncodeAsPieces(document)
        if join_on_whitespace:
            document_tokenized = " ".join(document_tokenized)
        return document_tokenized


def get_words_from_document(
    document: str,
    language: str,
    sentence_piece_tokenizer: SentencePieceTokenizer,
    need_to_lower: bool = True,
    strip_characters: Set[str] = set(),
) -> List[str]:
    """split word from document"""
    if language not in ["ZH"]:
        # 不是中文的话，才用空格\t等标记进行分词
        tokenizer = None
    else:
        # 只有中文才会使用sentence_piece_tokenizer进行分词
        tokenizer = sentence_piece_tokenizer

    if tokenizer:
        words = tokenizer.tokenize(document, join_on_whitespace=False)
    else:
        words = split_on_whitespace(document, new_line=True, tab=True)

    assert isinstance(words, list)

    if need_to_lower:
        words = [word.lower() for word in words]
    if strip_characters:
        words = [strip(word, strip_characters) for word in words]
        words = remove_empty_el_from_list(words)
    return words


def split_on_whitespace(
    document: str,
    new_line: bool = False,
    tab: bool = False,
) -> List[str]:
    """split document using whitespace"""
    sep = [" "] + new_line * ["\n"] + tab * ["\t"]
    sep_str = "|".join(sep)
    split_document = re.split(sep_str, document)
    split_document = remove_empty_el_from_list(split_document)
    return split_document


def remove_empty_el_from_list(list_: List[str]) -> List[str]:
    return [el for el in list_ if el]


def strip(document: str, strip_characters: Set[str]) -> str:
    """
    Way faster than document.strip(strip_characters)
    since strip_characters is now a set instead of a str,
    and it contains a lot of elements (all the emojis).
    """
    if not document:
        return document
    beg_ind = 0
    end_ind = len(document)
    for i in range(len(document)):
        if document[i] in strip_characters:
            beg_ind += 1
        else:
            break
    for i in range(1, len(document) + 1):
        if document[-i] in strip_characters:
            end_ind -= 1
        else:
            break
    document_stripped = document[beg_ind:end_ind]
    return document_stripped


def words_augmentation(words: List[str], group_size: int, join_char: str) -> List[str]:
    """Augment words, especially for Chinese (without a space between words)
    and Vietnamese (with a space between syllables)."""
    augmentation: List[str] = [
        join_char.join(words[i : i + group_size])
        for i in range(len(words) - group_size + 1)
    ]
    return augmentation


def get_augmentation_word_list(
    words: List[str], group_size_list: List[int], join_char: str
) -> List[str]:
    augmentation_list = [
        words_augmentation(words, group_size, join_char)
        for group_size in group_size_list
    ]
    return [word for augm in augmentation_list for word in augm]
