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
utility for
uploading content to bos
"""

from baidubce.auth.bce_credentials import BceCredentials
from baidubce.bce_client_configuration import BceClientConfiguration
from baidubce.services.bos.bos_client import BosClient


def upload_content_to_bos(
    data: str,
    remote_file_path: str,
    bucket_name: str,
    region: str,
    ak: str,
    sk: str,
) -> None:
    bos_config = BceClientConfiguration(
        credentials=BceCredentials(ak, sk), endpoint=f"{region}.bcebos.com"
    )
    BosClient(bos_config).put_object_from_string(bucket_name, remote_file_path, data)


def generate_bos_file_path(bucket_name: str, absolute_path: str) -> str:
    return f"bos:/{bucket_name}{absolute_path}"
