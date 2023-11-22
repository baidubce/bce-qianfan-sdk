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
    Preceding = "Preceding"
    """_summary_
    """
    Running = "Running"
    Done = "Done"
    Error = "Error"
    Stopped = "Stopped"


class FinetuneStatus(str, Enum):
    Unknown = "Unknown"
    """未知状态"""
    Created = "Created"
    """任务创建成功，对应创建任务+创建任务运行时API两部分都成功"""
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


class ServiceStatus(str, Enum):
    Unknown = "Unknown"
    """未知状态"""
    Deploying = "Deploying"
    """模型服务发布中"""
    Deployed = "Deployed"
    """模型服务发布成功"""
    DeployFailed = "DeployFailed"
    """模型服务发布失败"""
    DeployOffline = "DeployOffline"
    """服务下线"""


ModelTypeMapping = {
    "ERNIE-Bot-turbo-0725": "ERNIE-Bot-turbo",
    "ERNIE-Bot-turbo-0516": "ERNIE-Bot-turbo",
    "ERNIE-Bot-turbo-0704": "ERNIE-Bot-turbo",
    "Llama-2-7b": "Llama-2",
    "Llama-2-13b": "Llama-2",
    "SQLCoder-7B": "SQLCoder",
    "ChatGLM2-6B": "ChatGLM2",
    "Baichuan2-13B": "Baichuan2-13B",
    "BLOOMZ-7B": "BLOOMZ",
}


class ModelType(str, Enum):
    LLM = "LLM"
    Text2Image = "Text2Image"


class ServiceType(str, Enum):
    Chat = "Chat"
    Completion = "Completion"
    Embedding = "Embedding"
