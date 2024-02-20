// Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// # 百度千帆大模型平台 Go SDK
//
// 千帆SDK提供大模型工具链最佳实践，让AI工作流和AI原生应用优雅且便捷地访问千帆大模型平台。
// 目前 SDK 提供了以下功能：
//
// * 大模型推理：实现了对一言（ERNIE-Bot）系列、开源大模型等模型推理的接口封装，支持对话、补全、Embedding等。
package qianfan

// SDK 版本
const Version = "v0.0.2"
const versionIndicator = "qianfan_go_sdk_" + Version
