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
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from baidubce.auth.bce_credentials import BceCredentials
from baidubce.bce_client_configuration import BceClientConfiguration
from baidubce.services.bos.bos_client import BosClient

from qianfan import get_config
from qianfan.utils import log_info


class BosHelper:
    def __init__(
        self,
        region: Optional[str] = None,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
    ) -> None:
        if not region:
            region = get_config().BOS_HOST_REGION

        if not ak:
            ak = get_config().ACCESS_KEY

        if not sk:
            sk = get_config().SECRET_KEY

        bos_config = BceClientConfiguration(
            credentials=BceCredentials(ak, sk), endpoint=f"{region}.bcebos.com"
        )
        self.bos_client = BosClient(bos_config)

    def upload_content_to_bos(
        self,
        data: str,
        remote_file_path: str,
        bucket_name: str,
    ) -> None:
        """直接上传 str 到指定 BOS 路径"""
        self.bos_client.put_object_from_string(bucket_name, remote_file_path, data)

    def upload_file_to_bos(
        self,
        file_path: str,
        remote_file_path: str,
        bucket_name: str,
    ) -> None:
        """上传本地文件到指定 BOS 路径"""
        self.bos_client.put_object_from_file(bucket_name, remote_file_path, file_path)

    def get_bos_file_shared_url(
        self,
        remote_file_path: str,
        bucket_name: str,
    ) -> str:
        """获取 BOS 中的文件的分享链接，时效 30 分钟"""
        return self.bos_client.generate_pre_signed_url(
            bucket_name, remote_file_path
        ).decode("utf-8")

    def get_bos_bucket_location(
        self,
        bucket_name: str,
    ) -> str:
        """获取 BOS bucket 的 region"""
        return self.bos_client.get_bucket_location(bucket_name)

    def check_if_file_existed_on_bos(
        self,
        bucket: str,
        bos_file_path: str,
    ) -> bool:
        log_info(f"check if bos file {bos_file_path} existed")
        file_existed = True
        try:
            self.bos_client.get_object_meta_data(bucket, bos_file_path)
        except Exception:
            file_existed = False

        return file_existed

    def delete_bos_file_anyway(self, bucket: str, bos_file_path: str) -> None:
        try:
            self.bos_client.delete_object(bucket, bos_file_path)
        except Exception:
            # 防御性删除，不管文件是否是真的存在
            pass

    def get_metadata(self, bucket: str, file_path: str) -> Dict[str, Any]:
        actual_bos_file_path = file_path if file_path[0] != "/" else file_path[1:]
        return self.bos_client.get_object_meta_data(
            bucket, actual_bos_file_path
        ).metadata.__dict__

    def get_object_as_file(self, bucket: str, bos_path: str, local_path: str) -> None:
        actual_bos_file_path = bos_path if bos_path[0] != "/" else bos_path[1:]
        return self.bos_client.get_object_to_file(
            bucket, actual_bos_file_path, local_path
        )


def generate_bos_file_path(bucket_name: str, absolute_path: str) -> str:
    return f"bos:/{bucket_name}{absolute_path}"


def generate_bos_file_parent_path(bucket_name: str, absolute_path: str) -> str:
    p = Path(f"/{bucket_name}{absolute_path}")
    return f"bos:{p.parent}"


def is_valid_bos_path(path: str) -> bool:
    pattern = r"^bos:/([a-zA-Z0-9_-]+(\/)?)*$"
    match = re.match(pattern, path)

    if match:
        return True
    else:
        return False


def parse_bos_path(bos_path: str) -> Tuple[str, str]:
    """解析 bos 路径，返回 bucket 和 path"""
    if bos_path.startswith("bos://"):
        path = bos_path[6:]
    elif bos_path.startswith("bos:/"):
        path = bos_path[5:]
    else:
        raise ValueError(f"invalid bos path {bos_path}")
    index = path.find("/")
    return path[:index], path[index:]
