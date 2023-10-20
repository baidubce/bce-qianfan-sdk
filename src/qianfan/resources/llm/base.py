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
from typing import Any, AsyncIterator, Dict, Iterator, Optional, Set, Tuple, Union

import qianfan.errors as errors
from qianfan.consts import DefaultValue
from qianfan.resources.api_requestor import QfAPIRequestor
from qianfan.resources.typing import JsonBody, QfLLMInfo, QfResponse, RetryConfig
from qianfan.utils import log_warn

# This is used when user provides `endpoint`
# In such cases, SDK cannot know which model the user is using
# This constant is used to express no model is spcified,
# so that SDK still can get the requirements of API from _supported_models()
UNSPECIFIED_MODEL = "UNSPECIFIED_MODEL"


class BaseResource(object):
    """
    base class of Qianfan object
    """

    def __init__(
        self,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        init resource
        """
        self._model = model
        self._endpoint = endpoint
        self._client = QfAPIRequestor(**kwargs)

    def _update_model_and_endpoint(
        self, model: Optional[str], endpoint: Optional[str]
    ) -> Tuple[Optional[str], str]:
        """
        update model and endpoint from constructor
        """
        # if user do not provide new model and endpoint,
        # use the model and endpoint from constructor
        if model is None and endpoint is None:
            model = self._model
            endpoint = self._endpoint
        if endpoint is None:
            m = self._default_model() if model is None else model
            endpoint = self._supported_models()[m].endpoint
        else:
            endpoint = self._convert_endpoint(model, endpoint)
        return model, endpoint

    def _do(
        self,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        qianfan resource basic do

        Args:
            **kwargs (dict): kv dict data。

        """
        model, endpoint = self._update_model_and_endpoint(model, endpoint)
        self._check_params(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            **kwargs,
        )
        retry_config = RetryConfig(
            retry_count=retry_count,
            timeout=request_timeout,
            backoff_factor=backoff_factor,
        )
        endpoint = self._get_endpoint_from_dict(model, endpoint, stream, **kwargs)
        resp = self._client.llm(
            endpoint=endpoint,
            header=self._generate_header(model, endpoint, stream, **kwargs),
            query=self._generate_query(model, endpoint, stream, **kwargs),
            body=self._generate_body(model, endpoint, stream, **kwargs),
            stream=stream,
            data_postprocess=self._data_postprocess,
            retry_config=retry_config,
        )
        return resp

    async def _ado(
        self,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        qianfan aio resource basic do

        Args:
            **kwargs: kv dict data

        Returns:
            None

        """
        model, endpoint = self._update_model_and_endpoint(model, endpoint)
        self._check_params(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            **kwargs,
        )
        retry_config = RetryConfig(
            retry_count=retry_count,
            timeout=request_timeout,
            backoff_factor=backoff_factor,
        )
        endpoint = self._get_endpoint_from_dict(model, endpoint, stream, **kwargs)
        resp = await self._client.async_llm(
            endpoint=endpoint,
            header=self._generate_header(model, endpoint, stream, **kwargs),
            query=self._generate_query(model, endpoint, stream, **kwargs),
            body=self._generate_body(model, endpoint, stream, **kwargs),
            stream=stream,
            data_postprocess=self._data_postprocess,
            retry_config=retry_config,
        )
        return resp

    def _check_params(
        self,
        model: Optional[str],
        endpoint: Optional[str],
        stream: bool,
        retry_count: int,
        request_timeout: float,
        backoff_factor: float,
        **kwargs: Any,
    ) -> None:
        """
        check user provide params
        """
        if stream is True and retry_count != 1:
            raise errors.InvalidArgumentError(
                "retry is not available when stream is enabled"
            )

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
        """
        preset model list

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        raise NotImplementedError

    @classmethod
    def _default_model(cls) -> str:
        """
        default model

        Args:
            None

        Return:
            a str which is the default model name
        """
        raise NotImplementedError

    def _get_endpoint(self, model: str) -> QfLLMInfo:
        """
        get the endpoint of the given `model`

        Args:
            model (str): the name of the model,
                         must be defined in self._supported_models()

        Returns:
            str: the endpoint of the input `model`

        Raises:
            QianfanError: if the input is not in self._supported_models()
        """
        if model not in self._supported_models():
            if self._endpoint is not None:
                return QfLLMInfo(endpoint=self._endpoint)
            raise errors.InvalidArgumentError(
                f"The provided model `{model}` is not in the list of supported models."
                " If this is a recently added model, try using the `endpoint`"
                " arguments and create an issue to tell us. Supported models:"
                f" {self.models()}"
            )
        return self._supported_models()[model]

    def _get_endpoint_from_dict(
        self, model: Optional[str], endpoint: Optional[str], stream: bool, **kwargs: Any
    ) -> str:
        """
        extract the endpoint of the model in kwargs, or use the endpoint defined in
        __init__

        Args:
            **kwargs (dict): any dict

        Returns:
            str: the endpoint of the model in kwargs

        """
        if endpoint is not None:
            return endpoint
        if model is not None:
            return self._get_endpoint(model).endpoint
        return self._get_endpoint(self._default_model()).endpoint

    def _generate_header(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate header
        """
        if "header" in kwargs:
            return kwargs["header"]
        return {}

    def _generate_query(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate query
        """
        if "query" in kwargs:
            return kwargs["query"]
        return {}

    def _generate_body(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate body
        """
        kwargs = copy.deepcopy(kwargs)
        IGNORED_KEYS = {"headers", "query"}
        for key in IGNORED_KEYS:
            if key in kwargs:
                del kwargs[key]
        if model is not None and model in self._supported_models():
            model_info = self._supported_models()[model]
            # warn if user provide unexpected arguments
            for key in kwargs:
                if (
                    key not in model_info.required_keys
                    and key not in model_info.optional_keys
                ):
                    log_warn(
                        f"This key `{key}` does not seem to be a parameter that the"
                        f" model `{model}` will accept"
                    )
        else:
            default_model_info = self._supported_models()[self._default_model()]
            if endpoint == default_model_info.endpoint:
                model_info = default_model_info
            else:
                model_info = self._supported_models()[UNSPECIFIED_MODEL]

        for key in model_info.required_keys:
            if key not in kwargs:
                raise errors.ArgumentNotFoundError(
                    f"The required key `{key}` is not provided."
                )
        kwargs["stream"] = stream
        return kwargs

    def _data_postprocess(self, data: QfResponse) -> QfResponse:
        """
        post process data after get request response
        """
        return data

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert user-provided endpoint to real endpoint
        """
        raise NotImplementedError

    def models(self) -> Set[str]:
        """
        get all supported model names
        """
        models = set(self._supported_models().keys())
        models.remove(UNSPECIFIED_MODEL)
        return models

    def access_token(self) -> str:
        """
        get access token
        """
        return self._client._auth.access_token()
