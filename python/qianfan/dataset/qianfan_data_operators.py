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
data operator for qianfan online
"""


from qianfan.utils.pydantic import BaseModel, Field


class QianfanOperator(BaseModel):
    """Basic class for online ETL operator"""

    operator_name: str
    operator_type: str


class ExceptionRegulator(QianfanOperator):
    """Exception class for online ETL operator"""

    operator_type: str = "clean"


class Filter(QianfanOperator):
    """Filter class for online ETL operator"""

    operator_type: str = "filter"


class Deduplicator(QianfanOperator):
    """Deduplicator class for online ETL operator"""

    operator_type: str = "deduplication"


class DesensitizationProcessor(QianfanOperator):
    """Sensitive data processor class for online ETL operator"""

    operator_type: str = "desensitization"


class RemoveEmoji(ExceptionRegulator):
    """Exception class to remove emoji"""

    operator_name: str = "remove_emoji"


class RemoveInvisibleCharacter(ExceptionRegulator):
    """Exception class to remove invisible character"""

    operator_name: str = "remove_invisible_character"


class ReplaceUniformWhitespace(ExceptionRegulator):
    """Exception class to replace uniform whitespace"""

    operator_name: str = "replace_uniform_whitespace"


class RemoveNonMeaningCharacters(ExceptionRegulator):
    """Exception class to remove non-meaning characters"""

    operator_name: str = "remove_non_meaning_characters"


class ReplaceTraditionalChineseToSimplified(ExceptionRegulator):
    """Exception class to replace traditional chinese to simplified"""

    operator_name: str = "replace_traditional_chinese_to_simplified"


class RemoveWebIdentifiers(ExceptionRegulator):
    """Exception class to remove web identifiers"""

    operator_name: str = "remove_web_identifiers"


class FilterCheckNumberWords(Filter):
    """Filter class to check number of words"""

    operator_name: str = "filter_check_number_words"
    number_words_min_cutoff: int = Field(default=1)
    number_words_max_cutoff: int = Field(default=10000)


class FilterCheckWordRepetitionRemoval(Filter):
    """Filter class to check word repetition removal"""

    operator_name: str = "filter_check_word_repetition_removal"
    word_repetition_max_cutoff: float


class FilterCheckCharacterRepetitionRemoval(Filter):
    """Filter class to check character repetition removal"""

    operator_name: str = "filter_check_character_repetition_removal"
    default_character_repetition_max_cutoff: float


class FilterCheckSpecialCharacters(Filter):
    """Filter class to check special characters"""

    operator_name: str = "filter_check_special_characters"
    special_characters_max_cutoff: float


class FilterCheckFlaggedWords(Filter):
    """Filter class to check flagged words"""

    operator_name: str = "filter_check_flagged_words"
    flagged_words_max_cutoff: float


class FilterCheckLangId(Filter):
    """Filter class to check lang id"""

    operator_name: str = "filter_check_lang_id"
    lang_id_min_cutoff: float


class FilterCheckPerplexity(Filter):
    """Filter class to check perplexity"""

    operator_name: str = "filter_check_perplexity"
    perplexity_max_cutoff: int


class DeduplicationSimhash(Deduplicator):
    """Deduplicator class to deduplicate by simhash"""

    operator_name: str = "deduplication_simhash"
    distance: float


class ReplaceEmails(DesensitizationProcessor):
    """Sensitive data processor class to replace emails"""

    operator_name: str = "replace_emails"


class ReplaceIp(DesensitizationProcessor):
    """Sensitive data processor class to replace ip"""

    operator_name: str = "replace_ip"


class ReplaceIdentifier(DesensitizationProcessor):
    """Sensitive data processor class to replace identifier"""

    operator_name: str = "replace_identifier"
