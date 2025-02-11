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
"""
client typing
"""

from typing import Any, List, Optional

from typing_extensions import Literal

from qianfan.utils.pydantic import BaseModel, Field

__all__ = ["Completion"]


class Function(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: str
    function: Function


class SearchResult(BaseModel):
    index: int
    url: str
    title: str
    datasource_id: str


class ChatCompletionMessage(BaseModel):
    content: Optional[str] = None
    """The contents of the message."""

    reasoning_content: Optional[str] = None

    role: Literal["assistant"]
    """The role of the author of this message."""

    name: Optional[str] = None

    tool_calls: Optional[List[ToolCall]] = None

    tool_call_id: Optional[str] = None


class Choice(BaseModel):
    finish_reason: Optional[str] = None
    """The reason the model stopped generating tokens.
    "normal", "stop", "length", "tool_calls", "content_filter", "function_call"
    """

    index: int
    """The index of the choice in the list of choices."""

    message: ChatCompletionMessage
    """A chat completion message generated by the model."""

    ban_round: Optional[int] = None

    flag: Optional[int] = None


class CompletionUsage(BaseModel):
    completion_tokens: int
    """Number of tokens in the generated completion."""

    prompt_tokens: int
    """Number of tokens in the prompt."""

    total_tokens: int
    """Total number of tokens used in the request (prompt + completion)."""


class CompletionStatistic(BaseModel):
    first_token_latency: float = Field(default=0)
    """first token latency when using stream"""

    request_latency: float = Field(default=0)
    """
    it's response interval between current chunk and last chunk when streaming.
    Else it's api response elapsed time read from api
    """

    total_latency: float
    """total latency of request complete, it's based on clock on your system"""

    start_timestamp: float
    """the timestamp of request start"""

    avg_output_tokens_per_second: float
    """average output tokens per second"""


class Completion(BaseModel):
    id: str
    """A unique identifier for the chat completion."""

    choices: List[Choice]
    """A list of chat completion choices.

    Can be more than one if `n` is greater than 1.
    """

    created: int
    """The Unix timestamp (in seconds) of when the chat completion was created."""

    model: str
    """The model used for the chat completion."""

    object: Literal["chat.completion"]
    """The object type, which is always `chat.completion`."""

    usage: Optional[CompletionUsage] = None
    """Usage statistics for the completion request."""

    statistic: Optional[CompletionStatistic] = None

    raw: Any = None


class ChoiceDelta(BaseModel):
    content: Optional[str] = None
    """The contents of the message."""

    reasoning_content: Optional[str] = None

    tool_calls: Optional[List[ToolCall]] = None


class CompletionChunkChoice(BaseModel):
    delta: ChoiceDelta
    """A chat completion delta generated by streamed model responses."""

    finish_reason: Optional[
        Literal[
            "normal", "stop", "length", "tool_calls", "content_filter", "function_call"
        ]
    ] = None
    """The reason the model stopped generating tokens."""

    index: int
    """The index of the choice in the list of choices."""

    ban_round: Optional[int] = None

    flag: Optional[int] = None


class CompletionChunk(BaseModel):
    id: str
    """A unique identifier for the chat completion. Each chunk has the same ID."""

    choices: List[CompletionChunkChoice]
    """A list of chat completion choices."""

    created: int
    """The Unix timestamp (in seconds) of when the chat completion was created.

    Each chunk has the same timestamp.
    """

    model: str
    """The model to generate the completion."""

    object: str
    """The object type"""

    usage: Optional[CompletionUsage] = None
    """
    An optional field that will only be present when you set
    `stream_options: {"include_usage": true}` in your request. When present, it
    contains a null value except for the last chunk which contains the token usage
    statistics for the entire request.
    """

    statistic: Optional[CompletionStatistic] = None

    web_search: Optional[SearchResult] = None

    raw: Any = None
