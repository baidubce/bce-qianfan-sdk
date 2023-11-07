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
Tool API on Baidu Cloud
"""


import requests
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple, Union
from qianfan.resources.typing import QfRequest, QfResponse
from qianfan.resources.tools.utils import qianfan_api_request
from qianfan.resources.api_requestor import QfAPIRequestor
from qianfan.resources.auth import Auth
from qianfan import get_config
from qianfan.errors import InvalidArgumentError


def _extract_baidu_cloud_ak_sk(**kwargs: Any) -> Tuple[str, str]:
    ak = kwargs.get("ak") or get_config().BAIDU_CLOUD_AK
    sk = kwargs.get("sk") or get_config().BAIDU_CLOUD_SK
    if ak is None or sk is None:
        raise InvalidArgumentError("both ak and sk of baidu cloud must be set")
    kwargs.pop("ak", None)
    kwargs.pop("sk", None)
    return ak, sk


class Tools:
    """
    Tools API
    """

    @classmethod
    def translate(
        cls, text: str, target_language: str, src_language: str = "auto", **kwargs: Any
    ) -> str:
        ak, sk = _extract_baidu_cloud_ak_sk(**kwargs)
        req = QfRequest("POST", "https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1")
        req.json_body = {"from": src_language, "to": target_language, "q": text}
        resp = QfAPIRequestor()._request_api(req, ak, sk)
        return resp["result"]["trans_result"][0]["dst"]

    @classmethod
    def ocr(cls, img_url: str, **kwargs: Any) -> List[str]:
        ak, sk = _extract_baidu_cloud_ak_sk(**kwargs)
        auth = Auth(ak=ak, sk=sk)
        r = requests.post(
            "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic",
            params={
                "access_token": auth.access_token(),
            },
            data=urllib.parse.urlencode({"url": img_url}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        words = r.json()["words_result"]
        return [w["words"] for w in words]

    @classmethod
    def text_correction(cls, text: str, **kwargs: Any) -> List[str]:
        ak, sk = _extract_baidu_cloud_ak_sk(**kwargs)
        req = QfRequest(
            "POST", "https://aip.baidubce.com/rpc/2.0/nlp/v2/text_correction"
        )
        req.json_body = {"text": text}
        resp = QfAPIRequestor()._request_api(req, ak, sk)
        return resp["item"]["correct_query"]

    @classmethod
    def tts(
        cls, text: str, cuid: str = "test", ctp: int = 1, lan: str = "zh", **kwargs: Any
    ) -> bytes:
        ak, sk = _extract_baidu_cloud_ak_sk(**kwargs)
        auth = Auth(ak=ak, sk=sk)
        r = requests.post(
            "https://tsn.baidu.com/text2audio",
            data=urllib.parse.urlencode(
                {
                    "tex": text,
                    "tok": auth.access_token(),
                    "cuid": cuid,
                    "ctp": ctp,
                    "lan": lan,
                    **kwargs,
                }
            ),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return r.content

    @classmethod
    def text_similarity(cls, text1: str, text2: str, **kwargs: Any) -> float:
        ak, sk = _extract_baidu_cloud_ak_sk(**kwargs)
        req = QfRequest("POST", "https://aip.baidubce.com/rpc/2.0/nlp/v2/simnet")
        req.json_body = {"text_1": text1, "text_2": text2}
        resp = QfAPIRequestor()._request_api(req, ak, sk)
        return resp["score"]

    @classmethod
    def extract_address(cls, text: str, **kwargs: Any) -> Dict[str, Any]:
        ak, sk = _extract_baidu_cloud_ak_sk(**kwargs)
        req = QfRequest("POST", "https://aip.baidubce.com/rpc/2.0/nlp/v1/address")
        req.json_body = {"text": text}
        resp = QfAPIRequestor()._request_api(req, ak, sk)
        return resp.body
