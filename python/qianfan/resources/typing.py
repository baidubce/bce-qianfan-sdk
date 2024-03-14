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

import copy
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Set, Union

import aiohttp
import requests

from qianfan.errors import InvalidArgumentError

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec  # noqa: F401
else:
    from typing import ParamSpec  # noqa: F401

if sys.version_info < (3, 8):
    from typing_extensions import Literal  # noqa: F401
else:
    from typing import Literal  # noqa: F401

ParamsType = Dict[str, str]
HeadersType = Dict[str, str]
JsonBody = Dict[str, Any]


def default_field(obj: Any) -> Any:
    """
    return the default field of dataclasses
    """
    return field(default_factory=lambda: copy.copy(obj))


@dataclass
class RetryConfig:
    """
    The retry config used in SDK
    """

    retry_count: int = 1
    """
    retry count
    """
    timeout: float = 10
    """
    requests timeout in seconds
    """
    max_wait_interval: float = 120
    """
    the max wait interval in seconds
    Because exponential backoff retry policy is used, the actual wait 
    interval will be changed, this is limit the max wait interval.
    """
    backoff_factor: float = 1
    """
    backoff factor in exponential backoff retry policy
    """
    jitter: float = 1
    """
    jitter in exponential backoff jitter retry policy
    """
    retry_err_codes: Set[int] = default_field({})
    """
    API error codes used to catch for retrying
    """


@dataclass
class QfRequest:
    """
    Request object used in SDK
    """

    method: str
    url: str
    query: ParamsType = default_field({})
    headers: HeadersType = default_field({})
    json_body: JsonBody = default_field({})
    retry_config: RetryConfig = default_field(RetryConfig())

    def requests_args(self) -> Dict[str, Any]:
        """
        convert self to args of requests.request() or aiohttp.requests()
        """
        return {
            "method": self.method,
            "url": self.url,
            "params": self.query,
            "headers": self.headers,
            "json": self.json_body,
        }

    @classmethod
    def from_requests(cls, req: requests.PreparedRequest) -> "QfRequest":
        """
        convert requests.PreparedRequest to QfRequest object
        """
        return cls(
            req.method if req.method else "",
            req.url if req.url else "",
            {},
            dict(req.headers),
            {},
        )

    @classmethod
    def from_aiohttp(cls, req: aiohttp.RequestInfo) -> "QfRequest":
        """
        convert aiohttp.RequestInfo to QfRequest object
        """
        return cls(req.method, str(req.url), {}, dict(req.headers), {})


@dataclass
class QfResponse(Mapping):
    """
    Response from Qianfan API
    """

    code: int
    """
    The HTTP status code of the response.
    """

    headers: Dict[str, str] = default_field({})
    """
    A dictionary of HTTP headers included in the response.
    """

    body: JsonBody = default_field({})
    """
    The JSON-formatted body of the response.
    """

    statistic: Dict[str, Any] = default_field({})
    """
    key:
    `request_latency`: request elapsed time in seconds, or received elapsed time
        of each response if stream=True
    `first_token_latency`: first token elapsed time int seconds
        only existed in streaming calling
    `total_latency`: resource elapsed time int seconds, include request, serialization
        and the waiting time if `rate_limit` is set.
    """

    request: Optional[QfRequest] = default_field(None)
    """
    Original request
    """

    def __getitem__(self, item: str) -> Any:
        """
        get item by operator[]
        if the `item` is not the member of response, the `item` will be the key of
        `body`
        """
        try:
            return getattr(self, item)
        except AttributeError:
            pass
        if item in self.body:
            return self.body[item]
        raise KeyError(item)

    def __len__(self) -> int:
        """
        get len of response body
        """
        return len(self.body)

    def __iter__(self) -> Iterator[Any]:
        """
        iterate over response body
        """
        return iter(self.body)


@dataclass
class QfLLMInfo:
    """
    LLM info in SDK
    """

    endpoint: str
    required_keys: Set[str] = default_field(set())
    optional_keys: Set[str] = default_field(set())
    max_input_chars: Optional[int] = default_field(None)
    max_input_tokens: Optional[int] = default_field(None)
    depracated: bool = default_field(False)


class QfRole(Enum):
    """
    Role type supported in Qianfan
    """

    User = "user"
    Assistant = "assistant"
    Function = "function"


class QfMessages:
    """
    An auxiliary class for representing a list of messages in a chat model.

    Example usage:

    .. code-block:: python

      messages = QfMessages()
      # append a message by str
      messages.append("Hello!")
      # send the messages directly
      resp = qianfan.ChatCompletion().do(messages = messages)
      # append the response to the messages and continue the conversation
      messages.append(resp)
      messages.append("next message", role = QfRole.User) # role is optional

    """

    @dataclass
    class _Message:
        """
        Internal class to express message
        """

        role: Union[QfRole, str] = QfRole.User
        content: str = default_field("")
        extra: Dict[str, Any] = default_field({})

        def _to_dict(self) -> Dict[str, Any]:
            """
            convert message to a dict
            """
            role = self.role
            if isinstance(role, QfRole):
                role = role.value
            return {
                "role": role,
                "content": self.content,
                **self.extra,
            }

    def __init__(self) -> None:
        """
        Init QfMessages
        """
        self._msg_list: List[QfMessages._Message] = []

    def append(
        self, message: Union[str, QfResponse], role: Optional[Union[str, QfRole]] = None
    ) -> None:
        """
        Appends a message to the QfMessages object.

        Parameters:
          message (Union[str, QfResponse]):
            The message to be appended. It can be a string or a QfResponse object. When
            the object is a QfResponse object, the role of the message sender will be
            `QfRole.Assistant` by default, unless you specify the role using the 'role'
          role (Optional[Union[str, QfRole]]):
            An optional parameter to specify the role of the message sender. If not
            provided, the function will determine the role based on the existed message.

        Example usage can be found in the introduction of this class.
        """
        if isinstance(message, str):
            if len(self._msg_list) >= 1 and "function_call" in self._msg_list[-1].extra:
                # last message is function call, this message role should be function
                function_call = self._msg_list[-1].extra["function_call"]
                role = role if role is not None else QfRole.Function
                msg = QfMessages._Message(role=role, content=message)
                if "name" in function_call:
                    msg.extra["name"] = function_call["name"]
            else:
                role = role if role is not None else QfRole.User
                msg = QfMessages._Message(role=role, content=message)
            self._msg_list.append(msg)
        elif isinstance(message, QfResponse):
            try:
                role = role if role is not None else QfRole.Assistant
                msg = QfMessages._Message(role=role, content=message.body["result"])
                if "function_call" in message.body:
                    msg.extra["function_call"] = message.body["function_call"]
                self._msg_list.append(msg)
            except Exception:
                raise InvalidArgumentError("response not found in QfResponse")
        else:
            raise InvalidArgumentError(
                "Unsupported message type, only `str` and `QfResponse` are supported"
            )

    def _to_list(self) -> List[Dict[str, Any]]:
        """
        convert messages to list
        """
        return [msg._to_dict() for msg in self._msg_list]
