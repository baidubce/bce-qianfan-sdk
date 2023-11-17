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
    BosClient(bos_config).put_object(bucket_name, remote_file_path, data)


def generate_bos_file_path(bucket_name: str, absolute_path: str) -> str:
    return f"bos:/{bucket_name}{absolute_path}"
