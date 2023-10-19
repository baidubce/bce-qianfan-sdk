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

from typing import Any, Dict, Optional

import qianfan.errors as errors
from qianfan.resources.llm.base import UNSPECIFIED_MODEL, BaseResource
from qianfan.resources.typing import QfLLMInfo


class EBPlugin(BaseResource):
    """
    QianFan Plugin API Resource

    """

    def __init__(
        self, model: Optional[str] = None, endpoint: Optional[str] = None, **kwargs: Any
    ) -> None:
        """
        Init for Plugin
        `model` will not be accepted
        """
        if model is not None or endpoint is not None:
            raise errors.InvalidArgumentError("`model` is not supported for plugin")
        super().__init__(model, endpoint, **kwargs)

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
        """
        Only one endpoint provided for plugins

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        return {
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="/erniebot/plugins",
                required_keys={"messages", "plugins"},
                optional_keys={"user_id", "extra_data"},
            ),
        }

    @classmethod
    def _default_model(cls) -> str:
        """
        no default model for EBPlugin

        """
        return UNSPECIFIED_MODEL

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert endpoint to ChatCompletion API endpoint
        """
        return "/erniebot/plugins"

    def _check_params(
        self,
        model: Optional[str],
        endpoint: Optional[str],
        stream: bool,
        retry_count: int,
        request_timeout: float,
        backoff_factor: float,
        **kwargs: Dict[str, Any]
    ) -> None:
        """
        check params
        plugin does not support model and endpoint arguments
        """
        if model is not None or endpoint is not None:
            raise errors.InvalidArgumentError("model is not supported in plugin")
        return super()._check_params(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            **kwargs
        )
