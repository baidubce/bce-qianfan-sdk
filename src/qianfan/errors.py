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

"""the collection of errors for this library
"""

from typing import Any


class QianfanError(Exception):
    """Base exception class for the qianfan sdk."""

    pass


class NotImplmentError(QianfanError):
    """Exception that's raised when code not implemented."""

    pass


class APIError(QianfanError):
    """Base exception clas for the qianfan api error"""

    def __init__(self, error_code: int, error_msg: str, req_id: Any) -> None:
        """
        init with error code and error message from api response
        """
        self.error_code = error_code
        self.error_msg = error_msg
        self.req_id = req_id
        super().__init__(
            f"api return error, req_id: {self.req_id} code: {self.error_code }, msg:"
            f" {self.error_msg}"
        )


class RequestError(QianfanError):
    """Exception when api request is failed"""


class InvalidArgumentError(QianfanError):
    """Exception when the argument is invalid"""

    pass


class ArgumentNotFoundError(QianfanError):
    """Exception when the argument is not found"""


class RequestTimeoutError(QianfanError):
    """Exception when api request is timeout"""

    pass


class AccessTokenExpiredError(QianfanError):
    """Exception when access token is expired"""

    pass


class InternalError(QianfanError):
    """Exception when internal error occurs"""

    pass


class ValidationError(Exception):
    """Exception when validating failed"""

    ...


class QianfanRequestError(Exception):
    """Exception when request on qianfan failed"""

    ...


class FileSizeOverflow(Exception):
    """Exception when zip file is too big"""

    ...
