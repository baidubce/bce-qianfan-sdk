# Copyright (c) 2025 Baidu, Inc. All Rights Reserved.
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

from .completions import Completions

class BatchChat:

    def __init__(self, api_key: str):
        api_key = api_key or os.getenv("QIANFAN_API_KEY")
        if not api_key:
            raise ValueError("API key is required. Please set api_key or QIANFAN_API_KEY env var.")
        self.api_key = api_key
        pass


    def completions(self, messages: list[dict], model: str, timeout: int | None = None, **kwargs) -> str:
        resp = Completions(self.api_key).create(messages=messages, model=model, timeout= timeout, **kwargs)
        return resp.choices[0].message.content


    def completions_raw(self, messages: list[dict], model: str, timeout: int | None = None, **kwargs):
        resp = Completions(self.api_key).create(messages=messages, model=model, timeout= timeout, **kwargs)
        return resp