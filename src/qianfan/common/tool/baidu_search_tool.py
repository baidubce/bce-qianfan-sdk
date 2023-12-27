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
baidu search tool
"""

from typing import Any, Dict, List, Optional, Union

from qianfan import ChatCompletion, Completion, QfResponse
from qianfan.common.tool.base_tool import BaseTool, ToolParameter


class BaiduSearchTool(BaseTool):
    """
    BaiduSearch is a search engine
    that can retrieve any information on the internet.
    """

    name: str = "baidu_search"
    description: str = "使用百度搜索引擎，在互联网上检索任何实时最新的相关信息"
    parameters: List[ToolParameter] = [
        ToolParameter(
            name="search_query",
            type="string",
            description="搜索的关键词或短语",
            required=True,
        )
    ]
    client: Union[Completion, ChatCompletion]

    def __init__(
        self,
        top_n: int = 2,
        channel: str = "normal",
        client: Optional[Union[Completion, ChatCompletion]] = None,
        with_reference: bool = False,
    ):
        """
        :param top_n: top n results which will be retrieved
        :param channel: the search channel
        :param client: the model client will be used to summarize the results
        :param with_reference: whether return reference in the tool output
        """
        self.top_n = top_n
        self.channel = channel
        if client is None:
            self.client = Completion(model="ERNIE-Bot-turbo")
        else:
            self.client = client
        self.with_reference = with_reference

    def run(self, parameters: Dict[str, str] = {}) -> Union[str, Dict[str, Any]]:
        """
        Run the tool and get the summary and reference of the search query
        """
        query = parameters["search_query"]
        tool_params: Dict[str, Any] = {
            "tools": [
                {
                    "type": "tool",
                    "tool": {
                        "name": "baidu_search",
                        "baidu_search": {
                            "channel": self.channel,
                            "top_n": self.top_n,
                        },
                    },
                }
            ],
            "tool_choice": {
                "type": "tool",
                "tool": {
                    "name": "baidu_search",
                },
            },
        }
        if isinstance(self.client, Completion):
            resp = self.client.do(prompt=query, **tool_params)
        else:  # isinstance(self.client, ChatCompletion)
            resp = self.client.do(
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                **tool_params
            )
        assert isinstance(resp, QfResponse)

        if not self.with_reference:
            return resp["result"]

        reference = []
        if "tools_info" in resp and resp["tools_info"]["name"] == "baidu_search":
            reference = resp["tools_info"]["baidu_search"]

        return {
            "summary": resp["result"],
            "reference": reference,
        }
