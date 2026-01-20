from enum import Enum
from typing import Any, Optional

from qianfan.model.consts import ServiceType
from qianfan.resources.console import consts as console_consts
from qianfan.utils.pydantic import BaseModel


class PaymentType(str, Enum):
    Prepaid = "Prepaid"
    Postpaid = "Postpaid"


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
    resource_type: str = "GPU-1-1"
    """
    deploy config resource type
    """
    region: Optional[str] = None
    """
    resource region
    """
    payment_type: str = PaymentType.Prepaid.value
    """
    billing payment type
    """
    months: int = 1
    """
    deploy months 
    """
    hours: Optional[int] = None
    """
    deprecated, use months instead
    deploy hours
    """
    auto_renew: bool = False
    """
    whether renew service automatically when expired
    """
    auto_renew_time_unit: str = "Month"
    """
    renew time unit
    """
    auto_renew_time: int = 1
    """
    renew time
    """
    charge_type: str = "ComputingUnit"
    """
    postpaid charge type
    """
    release_time: Optional[str] = None
    """
    postpaid release time
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
