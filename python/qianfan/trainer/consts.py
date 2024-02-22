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
from enum import Enum


class ActionState(str, Enum):
    """
    This class list the key point during an action execution
    At default, ActionState should be get through event_handler's
    dispatched event.
    """

    Preceding = "Preceding"
    """`Preceding` stands for the point before exec"""
    Running = "Running"
    """`Running` stands for the point during exec"""
    Done = "Done"
    """`Done` stands for the state of doing exec"""
    Error = "Error"
    """`Error` stands for the state when errors occur."""
    Stopped = "Stopped"
    """`Stopped` stands for the state when stop() is called."""


class TrainStatus(str, Enum):
    Unknown = "Unknown"
    """未知状态"""
    DatasetLoading = "DatasetLoading"
    """数据集加载中"""
    DatasetLoaded = "DatasetLoaded"
    """数据集加载完成"""
    DatasetLoadFailed = "DatasetLoadFailed"
    """数据集加载失败"""
    DatasetLoadStopped = "DatasetLoadStopped"
    """数据集停止加载"""
    TrainCreated = "TrainCreated"
    """任务创建，初始化"""
    Training = "Training"
    """训练中 对应训练任务运行时API状态的Running"""
    TrainFinished = "TrainFinished"
    """训练完成 对应训练任务运行时API的状态的Done"""
    TrainFailed = "TrainFailed"
    """训练任务失败，对应训练任务运行时API的状态的Failed"""
    TrainStopped = "TrainStopped"
    """训练任务失败，对应训练任务运行时API的状态的Stop"""
    ModelPublishing = "ModelPublishing"
    """模型发布中，对应获取模型运行时的Creating"""
    ModelPublishFailed = "ModelPublishFailed"
    """模型发布失败"""
    ModelPublished = "ModelPublished"
    """模型发布成功"""
    EvaluationCreated = "EvaluationCreated"
    """评估任务创建，初始化"""
    EvaluationRunning = "EvaluationRunning"
    """模型服务评估中"""
    EvaluationFailed = "EvaluationFailed"
    """模型服务评估失败"""
    EvaluationStopped = "EvaluationStopped"
    """模型服务评估停止"""
    EvaluationFinished = "EvaluationFinished"
    """模型服务评估完成"""


class ServiceStatus(str, Enum):
    Unknown = "Unknown"
    """未知状态"""
    Created = "Created"
    """任务创建，初始化"""
    Deploying = "Deploying"
    """模型服务发布中"""
    Deployed = "Deployed"
    """模型服务发布成功"""
    DeployFailed = "DeployFailed"
    """模型服务发布失败"""
    DeployStopped = "DeployStopped"
    """服务发布任务停止"""


class PeftType(str, Enum):
    ALL = "FullFineTuning"
    """全量更新"""
    PTuning = "PromptTuning"
    """p-tuning"""
    LoRA = "LoRA"
    """LoRA"""


class ServiceType(str, Enum):
    Chat = "Chat"
    """Corresponding to the `ChatCompletion`"""
    Completion = "Completion"
    """Corresponding to the `Completion`"""
    Embedding = "Embedding"
    """Corresponding to the `Embedding`"""
    Text2Image = "Text2Image"
    """Corresponding to the `Text2Image"""


StopMessage = "STOP"
# trainer 本地缓存
QianfanTrainerLocalCacheDir = ".qianfan_trainer_cache"
