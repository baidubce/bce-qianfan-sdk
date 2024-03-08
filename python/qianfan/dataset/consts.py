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
constants for dataset using
"""
from pathlib import Path

# 千帆本地缓存文件夹的绝对路径
QianfanLocalCacheDir = Path.home() / ".qianfan_cache"

# 千帆数据集本地缓存文件夹的绝对路径
QianfanDatasetLocalCacheDir = QianfanLocalCacheDir / "dataset"

QianfanMapperCacheDir = QianfanDatasetLocalCacheDir / ".mapper_cache"

# 千帆数据集下载缓存的存储路径
QianfanDatasetDownloadingCacheDir = (
    QianfanDatasetLocalCacheDir / ".qianfan_download_cache"
)

# Bos 数据源使用的缓存目录
QianfanDatasetBosCacheDir = QianfanDatasetLocalCacheDir / ".bos_cache"

# Bos 数据源使用的上传目录
QianfanDatasetBosUploadingCacheDir = QianfanDatasetBosCacheDir / "uploading"

# Bos 数据源使用的下载目录
QianfanDatasetBosDownloadingCacheDir = QianfanDatasetBosCacheDir / "downloading"

# 本地缓存中，元数据的后缀名
QianfanDatasetMetaInfoExtensionName = ".meta"

# 本地缓存中，缓存文件的后缀名
QianfanDatasetCacheFileExtensionName = ".arrow"

# 包装成单列表时使用的列名
QianfanDatasetPackColumnName = "_pack"

# 分组时应用的列名
QianfanDataGroupColumnName = "_group"

# 批量推理结果中，实际输入 Prompt 的列名
NewInputPromptColumnName = "input_prompt"

# 批量推理结果中，实际输入对话的列名
NewInputChatColumnName = "input_chats"

# 批量推理结果中，大模型输出结果的列名
LLMOutputColumnName = "llm_output"

# 批量推理结果中，预期结果的列名
OldReferenceColumnName = "expected_output"

# 批量推理结果中，请求耗时的列名
RequestLatencyColumnName = "request_complete_latency"

# 批量推理结果中，首 token 耗时的列名
FirstTokenLatencyColumnName = "first_token_latency"

# 批量推理结果中，用于标注不同模型结果的列名
LLMTagColumnName = "llm_tag"
