from typing import Any

from qianfan.model.consts import ServiceType
from qianfan.resources.console import consts as console_consts
from qianfan.utils.pydantic import BaseModel


class DeployConfig(BaseModel):
    name: str = ""
    """
    Service name
    """
    endpoint_prefix: str = ""
    """
    Endpoint custom prefix, will be used to call resource api
    """
    description: str = ""
    """
    description of service
    """
    replicas: int = 1
    """
    replicas for model services, related to the capacity in QPS of model service.
        default set to 1
    """
    pool_type: console_consts.DeployPoolType = (
        console_consts.DeployPoolType.PrivateResource
    )
    """
    resource pool type, public resource will be shared with others.
    """
    service_type: ServiceType
    """
    service type, after deploy, Service could behave like the specific type.
    """
    extras: Any = None
