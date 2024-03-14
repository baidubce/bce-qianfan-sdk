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
RPM & TPM API
"""
from typing import Any, Optional

from qianfan.consts import Consts
from qianfan.resources.console.utils import console_api_request
from qianfan.resources.typing import QfRequest


class Charge(object):
    """
    Class for Charging API
    """

    @classmethod
    @console_api_request
    def charge(cls, model: str, purchase_count: int, **kwargs: Any) -> QfRequest:
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
        req = QfRequest(method="POST", url=Consts.ChargeAPI)
        req.query = {"Action": Consts.ChargePurchaseQueryParam}
        req.json_body = {
            "model": model,
            "purchaseCount": purchase_count,
            "billing": {"paymentTiming": "Postpaid"},
            **kwargs,
        }
        return req

    @classmethod
    @console_api_request
    def info(
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

        req = QfRequest(method="POST", url=Consts.ChargeAPI)
        req.query = {"Action": Consts.ChargeInfoQueryParam}
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
    def stop(cls, model: str, instance_id: str, **kwargs: Any) -> QfRequest:
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

        req = QfRequest(method="POST", url=Consts.ChargeAPI)
        req.query = {"Action": Consts.ChargeStopQueryParam}
        req.json_body = {
            "model": model,
            "instanceId": instance_id,
        }

        return req
