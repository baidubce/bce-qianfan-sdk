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
wikipedia tool
"""

from typing import Dict, List, Optional

from qianfan.common.tool.base_tool import BaseTool, ToolParameter
from qianfan.utils.utils import assert_package_installed


class WikipediaTool(BaseTool):
    """
    Wikipedia is the world's largest encyclopedia that can search for any knowledge.
    """

    WIKIPEDIA_MAX_QUERY_LENGTH = 300

    name: str = "wikipedia"
    description: str = (
        "在维基百科上查询有关[人物、地点、公司、事实、历史事件或其他主题]的百科知识"
    )
    parameters: List[ToolParameter] = [
        ToolParameter(
            name="search_keyword",
            type="string",
            description="查询的目标关键词，可以是人物、地点、公司、事实、历史事件或其他主题",
            required=True,
        )
    ]

    def __init__(
        self,
        max_results: int = 3,
        wiki_max_length: int = 1000,
        result_max_length: int = 2000,
    ):
        """
        :param max_results: maximum number of results to return
        :param wiki_max_length: maximum length of the wikipedia content
        :param result_max_length: maximum length of the result
        """
        assert_package_installed("wikipedia")
        self.max_results = max_results
        self.wiki_max_length = wiki_max_length
        self.result_max_length = result_max_length

    def run(self, parameters: Dict[str, str] = {}) -> List[Dict[str, str]]:
        import wikipedia

        query = parameters["search_keyword"][: self.WIKIPEDIA_MAX_QUERY_LENGTH]
        search_results = wikipedia.search(query, results=self.max_results)
        results = []
        for result_title in search_results[: self.max_results]:
            wiki_content = self._get_wiki_content(result_title)
            if wiki_content:
                results.append(
                    {
                        "title": result_title,
                        "content": wiki_content[: self.wiki_max_length],
                    }
                )

        total_length = 0
        for result in results:
            if total_length + len(result["content"]) > self.result_max_length:
                result["content"] = result["content"][
                    : self.result_max_length - total_length
                ]
                break
            total_length += len(result["content"])

        return results

    @staticmethod
    def _get_wiki_content(page: str) -> Optional[str]:
        import wikipedia
        import wikipedia.exceptions as ex

        try:
            return wikipedia.page(title=page, auto_suggest=False).summary
        except (ex.PageError, ex.DisambiguationError):
            return None
