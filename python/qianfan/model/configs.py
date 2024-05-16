from typing import Any, Optional

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
    deprecated, use endpoint_suffix instead
    Endpoint custom prefix, will be used to call resource api
    """
    endpoint_suffix: str = ""
    """
    Endpoint custom suffix, will be used to call resource api
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
    qps: Optional[float] = None
    """
    qps
    use default model service's qps if not set
    """
    resource_type: str = "GPU-I-2"
    """
    deploy config resource type
    'GPU-I-2' or 'GPU-I-4', 'CPU-I-2'
    """
    months: Optional[int] = None
    """
    deploy months 
    """
    hours: Optional[int] = 1
    """
    deploy hours
    """
    pool_type: console_consts.DeployPoolType = (
        console_consts.DeployPoolType.PrivateResource
    )
    """
    deprecated
    resource pool type, public resource will be shared with others.
    """
    service_type: ServiceType
    """
    service type, after deploy, Service could behave like the specific type.
    """
    extras: Any = None
