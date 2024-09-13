# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
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
Charging API, including RPM & TPM, service deployment.
"""
from typing import Any, Dict, Optional

from qianfan.consts import Consts
from qianfan.resources.console.utils import console_api_request
from qianfan.resources.typing import QfRequest


class Charge(object):
    """
    Class for Charging API
    """

    @classmethod
    @console_api_request
    def charge_tpm_credit(
        cls, model: str, purchase_count: int, **kwargs: Any
    ) -> QfRequest:
        """
        charge the rpm / tpm credit.

        Parameters:
          model (str):
            The model you want to charge to.
          purchase_count (int):
            how many credit you want to charge.
          kwargs (Any):
            Additional keyword arguments.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/pltmk8zoc
        """
        req = QfRequest(method="POST", url=Consts.TpmCreditAPI)
        req.query = {"Action": Consts.TpmCreditPurchaseQueryParam}
        req.json_body = {
            "model": model,
            "purchaseCount": purchase_count,
            "billing": {"paymentTiming": "Postpaid"},
            **kwargs,
        }
        return req

    @classmethod
    @console_api_request
    def tpm_credit_info(
        cls,
        model: str,
        payment_type: Optional[str] = None,
        instance_id: Optional[str] = None,
        **kwargs: Any
    ) -> QfRequest:
        """
        query the rpm / tpm limit info

        Parameters:
            model (str):
                The model you want to get info.
            payment_type (Optional[str]):
                Which type of payment you want to get, default to None.
                Only available type is "Postpaid" currently.
            instance_id (Optional[str]):
                which specific instance you want to get.
            **kwargs (Any):
                Additional keyword arguments.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/oltmo6eq4
        """

        req = QfRequest(method="POST", url=Consts.TpmCreditAPI)
        req.query = {"Action": Consts.TpmCreditInfoQueryParam}
        req.json_body = {
            "model": model,
        }

        if payment_type and payment_type == "Postpaid":
            req.json_body["paymentTiming"] = payment_type

        if instance_id:
            req.json_body["instanceId"] = instance_id

        return req

    @classmethod
    @console_api_request
    def stop_tpm_credit_charging(
        cls, model: str, instance_id: str, **kwargs: Any
    ) -> QfRequest:
        """
        stop the rpm / tpm charging

        Parameters:
            model (str):
                The model you want to stop relative payment.
            instance_id (str):
                which specific instance you want to get.
            **kwargs (Any):
                Additional keyword arguments.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/oltmo6eq4
        """

        req = QfRequest(method="POST", url=Consts.TpmCreditAPI)
        req.query = {"Action": Consts.TpmCreditStopQueryParam}
        req.json_body = {
            "model": model,
            "instanceId": instance_id,
        }

        return req

    @classmethod
    @console_api_request
    def purchase_service_resource(
        cls, service_id: str, billing: Dict[str, Any], replicas: int, **kwargs: Any
    ) -> QfRequest:
        """
        purchase private service resource from qianfan

        Parameters:
            service_id (str):
                The service id which needs to buy private service resource
            billing (Dict[str, Any]):
                Purchase info.
            replicas (int):
                How many replica the user want to get.
            **kwargs (Any):
                other arguments

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/4lvuk0kxi
        """

        req = QfRequest(method="POST", url=Consts.PrivateResourceAPI)
        req.query = {"Action": Consts.PrivateResourcePurchaseParam}
        req.json_body = {
            "serviceId": service_id,
            "billing": billing,
            "replicasCount": replicas,
        }

        return req

    @classmethod
    @console_api_request
    def ger_service_resource_list(
        cls, service_id: str, payment_timing: Optional[str] = None, **kwargs: Any
    ) -> QfRequest:
        """
        get service resource info list

        Parameters:
            service_id (str):
                The service id which needs to buy private service resource
            payment_timing (Optional[str]):
                This parameter's value can only be either None or "Prepaid".
                Default to None
            **kwargs (Any):
                other arguments

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/klvuk3qob
        """

        req = QfRequest(method="POST", url=Consts.PrivateResourceAPI)
        req.query = {"Action": Consts.PrivateResourceGetResourceListParam}
        req.json_body = {
            "serviceId": service_id,
            "paymentTiming": payment_timing,
        }

        return req

    @classmethod
    @console_api_request
    def get_service_resource_instance_info(
        cls, service_id: str, instance_id: str, **kwargs: Any
    ) -> QfRequest:
        """
        purchase private service resource from qianfan

        Parameters:
            service_id (str):
                The service id which needs to buy private service resource
            instance_id (str):
                The resource instance id.
            **kwargs (Any):
                other arguments

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/4lvuk0kxi
        """

        req = QfRequest(method="POST", url=Consts.PrivateResourceAPI)
        req.query = {"Action": Consts.PrivateResourceGetResourceParam}
        req.json_body = {
            "serviceId": service_id,
            "instanceId": instance_id,
        }

        return req

    @classmethod
    @console_api_request
    def release_service_resource_instance_info(
        cls, service_id: str, instance_id: str, **kwargs: Any
    ) -> QfRequest:
        """
        release purchase private service resource from qianfan

        Parameters:
            service_id (str):
                The service id which needs to buy private service resource
            instance_id (str):
                The resource instance id.
            **kwargs (Any):
                other arguments

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/4lvuk0kxi
        """

        req = QfRequest(method="POST", url=Consts.PrivateResourceAPI)
        req.query = {"Action": Consts.PrivateResourceReleaseServiceResourceParam}
        req.json_body = {
            "serviceId": service_id,
            "instanceId": instance_id,
        }

        return req

    @classmethod
    @console_api_request
    def create_auto_renew_rules(
        cls,
        instance_id: str,
        instance_type: str,
        auto_renew_time_unit: Optional[str] = None,
        auto_renew_time: Optional[int] = None,
        **kwargs: Any
    ) -> QfRequest:
        """
        create a new automatically renew rules for resource

        Parameters:
            instance_id (str):
                The resource instance id.
            instance_type (str):
                Type of instance, can be "ComputingUnit" or "TPM".
            auto_renew_time_unit (Optional[str]):
                Time unit for automatically renew cycle. Default to None.
            auto_renew_time (Optional[int]):
                Time to renew. Default to None.
            **kwargs (Any):
                other arguments

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.
        """

        req = QfRequest(method="POST", url=Consts.PrivateResourceAPI)
        req.query = {"Action": Consts.PrivateResourceCreateAutoRenewRulesParam}
        req.json_body = {
            "instanceId": instance_id,
            "instanceType": instance_type,
        }

        if auto_renew_time_unit is not None and auto_renew_time is not None:
            req.json_body.update(
                {
                    "autoRenewTimeUnit": auto_renew_time_unit,
                    "autoRenewTime": auto_renew_time,
                }
            )

        return req
