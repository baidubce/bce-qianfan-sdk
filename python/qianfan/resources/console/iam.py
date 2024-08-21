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
iam API
"""
from typing import Any

from qianfan.config import get_config
from qianfan.consts import Consts
from qianfan.resources.console.utils import console_api_request
from qianfan.resources.typing import QfRequest, QfResponse


class IAM(object):
    @classmethod
    def create_bearer_token(
        cls,
        expire_in_seconds: int = 1000,
        **kwargs: Any,
    ) -> QfResponse:
        """
        create a bearer token for call api v2.

        Parameters:
        expire_in_seconds (int):
            expire time of the token, in seconds.
        kwargs:
            Additional keyword arguments that can be passed to customize the
            request.
        """
        kwargs["host"] = get_config().IAM_BASE_URL
        return cls._iam_call(
            req=QfRequest(
                method="GET",
                url=Consts.IAMBearerTokenAPI,
                query={
                    "expireInSeconds": str(expire_in_seconds),
                },
            ),
            **kwargs,
        )

    @classmethod
    @console_api_request
    def _iam_call(cls, req: QfRequest, **kwargs: Any) -> QfRequest:
        """
        inner caller for iam api, which accept a new host for iam api.
        The `@console_api_request` decorator is applied to this method, enabling
        it to send the generated QfRequest and return a QfResponse to the user.
        """
        return req
