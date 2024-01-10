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
duck duck go search tool
"""

from typing import Dict, List, Optional

from qianfan.common.tool.base_tool import BaseTool, ToolParameter
from qianfan.utils.utils import assert_package_installed


class DuckDuckGoSearchTool(BaseTool):
    """
    DuckDuckGoSearch is a search engine
    that can retrieve any information on the internet.
    """

    name: str = "duckduckgo_search"
    description: str = "使用DuckDuckGo搜索引擎在互联网上检索任何信息"
    parameters: List[ToolParameter] = [
        ToolParameter(
            name="search_query",
            type="string",
            description="搜索的关键词或短语",
            required=True,
        )
    ]

    def __init__(
        self,
        return_url: bool = False,
        region: str = "wt-wt",
        safe_search: str = "moderate",
        backend: str = "html",
        timelimit: Optional[str] = None,
        max_results: int = 3,
    ):
        """
        :param return_url: whether to return the url of the search result
        :param region: region to search in
        :param safe_search: safe search level
        :param backend: backend to use
        :param timelimit: time limit
        :param max_results: maximum number of results to return
        """
        assert_package_installed("duckduckgo_search")
        self.return_url = return_url
        self.region = region
        self.safe_search = safe_search
        self.backend = backend
        self.timelimit: Optional[str] = timelimit
        self.max_results = max_results

    def run(self, parameters: Dict[str, str] = {}) -> List[Dict[str, str]]:
        from duckduckgo_search import DDGS

        with DDGS() as client:
            response = client.text(
                keywords=parameters["search_query"],
                region=self.region,
                safesearch=self.safe_search,
                timelimit=self.timelimit,
                max_results=self.max_results,
                backend=self.backend,
            )
            if response:
                return [
                    {
                        "title": record["title"],
                        "content": record["body"],
                        **({"url": record["href"]} if self.return_url else {}),
                    }
                    for record in response
                ]
        return []
