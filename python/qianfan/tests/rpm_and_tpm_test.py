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
    Unit test for RPM and TPM
"""

from qianfan.resources.console.charge import Charge


def test_charge():
    """
    test charge.Charge
    """

    model = "ernie-4.0-8k"
    count = 10
    resp = Charge.charge_tpm_credit(model, count, {"paymentTiming": "Postpaid"})
    assert resp["_request"]["model"] == model
    assert resp["_request"]["purchaseCount"] == count
    assert resp["_request"]["billing"]["paymentTiming"] == "Postpaid"


def test_info():
    """
    test Charge.info
    """

    model = "ernie-4.0-8k"
    wrong_payment_type = "wrong_payment_type"

    resp = Charge.tpm_credit_info(model, wrong_payment_type)
    assert resp["_request"]["model"] == model
    assert "paymentTiming" not in resp["_request"]


def test_stop():
    """
    test Charge.stop
    """

    model = "ernie-4.0-8k"
    instance_id = "instance_id"

    resp = Charge.stop_tpm_credit_charging(model, instance_id)
    assert resp["_request"]["model"] == model
    assert resp["_request"]["instanceId"] == instance_id
