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
Service API
"""

from typing import Any, List, Optional, Union

from qianfan.consts import Consts
from qianfan.errors import InvalidArgumentError
from qianfan.resources.console.consts import DeployPoolType, ServiceType
from qianfan.resources.console.utils import console_api_request
from qianfan.resources.typing import QfRequest


class Service(object):
    """
    Class for Service API
    """

    @classmethod
    @console_api_request
    def create(
        cls,
        model_id: Union[int, str],
        model_version_id: Union[int, str],
        name: str,
        uri: str,
        replicas: int,
        pool_type: DeployPoolType = DeployPoolType.PrivateResource,
        description: Optional[str] = None,
        **kwargs: Any
    ) -> QfRequest:
        """
        Create a service for the given model.

        This function creates a service associated with the specified model and
        iteration.

        Parameters:
          model_id (int):
            The ID of the model for which the service is to be created.
          model_version_id (int):
            The ID of the version of the model.
          name (str):
            The name for the created service.
          uri (str):
            The URI (Uniform Resource Identifier) for accessing the service.
          replicas (int):
            The number of replicas for the service.
          pool_type (int):
            The type of pooling for the service (1 for public and 2 for private).
          description (Optional[str], optional):
            An optional description for the service.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Plnlmxdgy
        """
        req = QfRequest(method="POST", url=Consts.ServiceCreateAPI)
        req.json_body = {
            "modelId": model_id,
            "modelVersionId": model_version_id,
            "name": name,
            "uri": uri,
            "replicas": replicas,
            "poolType": pool_type.value,
            **kwargs,
        }
        if description is not None:
            req.json_body["description"] = description
        return req

    @classmethod
    @console_api_request
    def get(cls, id: int, **kwargs: Any) -> QfRequest:
        """
        Retrieve information for a specific service.

        This method allows retrieval of information pertaining to a specific service
        based on its unique identifier.

        Parameters:
          id (int):
            The unique identifier for the service.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/llnlmyp8o
        """
        req = QfRequest(method="POST", url=Consts.ServiceDetailAPI)
        req.json_body = {
            "serviceId": id,
            **kwargs,
        }
        return req

    @classmethod
    @console_api_request
    def list(
        cls,
        api_type_filter: Optional[List[Union[str, ServiceType]]] = None,
        **kwargs: Any
    ) -> QfRequest:
        """
        list all services.

        This method allows calling list API to get all services, including
        `common`: preset model services.
        `custom` user-deployed model services.

        Parameters:
          api_type_filter (Optional[List[str]]):
            Optional, filter the services by ServiceType.
              Concretely, the value of this parameter can be one or more of:
                'chat', 'completions', 'embeddings', 'text2image', 'image2text'
              If the value is `None`, all services will be returned.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/4lqoklvr1
        """
        req = QfRequest(method="POST", url=Consts.ServiceListAPI)
        req.json_body = {
            **kwargs,
        }
        if api_type_filter is not None:
            for i, type in enumerate(api_type_filter):
                if isinstance(type, str):
                    pass
                elif isinstance(type, ServiceType):
                    api_type_filter[i] = type.value
                else:
                    raise InvalidArgumentError("Invalid api type: {}".format(type))
            req.json_body["apiTypefilter"] = api_type_filter
        return req
