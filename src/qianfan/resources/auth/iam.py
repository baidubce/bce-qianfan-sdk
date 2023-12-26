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
IAM related functions
"""

import time

from baidubce.auth.bce_credentials import BceCredentials
from baidubce.auth.bce_v1_signer import sign
from baidubce.utils import get_canonical_time

from qianfan import get_config
from qianfan.resources.typing import QfRequest


def iam_sign(
    ak: str,
    sk: str,
    request: QfRequest,
) -> None:
    """
    Create the authorization
    """
    credentials = BceCredentials(ak, sk)
    timestamp = time.time()
    x_bce_date = get_canonical_time(timestamp)
    request.headers["x-bce-date"] = x_bce_date.decode()

    authorization = sign(
        credentials,
        str.encode(request.method),
        str.encode(request.url),
        {str.encode(k): v for k, v in request.headers.items()},
        {str.encode(k): v for k, v in request.query.items()},
        timestamp=timestamp,
        expiration_in_seconds=get_config().IAM_SIGN_EXPIRATION_SEC,
        headers_to_sign={str.encode(k.lower()) for k in request.headers.keys()},
    )

    request.headers["Authorization"] = authorization.decode()
