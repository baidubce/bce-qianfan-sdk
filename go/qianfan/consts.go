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

package qianfan

// 模型请求的前缀
const (
	modelAPIPrefix = "/rpc/2.0/ai_custom/v1/wenxinworkshop"
	authAPIPrefix  = "/oauth/2.0/token"
)

// 默认使用的模型
const (
	DefaultChatCompletionModel = "ERNIE-Bot-turbo"
	DefaultCompletionModel     = "ERNIE-Bot-turbo"
	DefaultEmbeddingModel      = "Embedding-V1"
)

// API 错误码
const (
	NoErrorErrCode                    = 0
	UnknownErrorErrCode               = 1
	ServiceUnavailableErrCode         = 2
	UnsupportedMethodErrCode          = 3
	RequestLimitReachedErrCode        = 4
	NoPermissionToAccessDataErrCode   = 6
	GetServiceTokenFailedErrCode      = 13
	AppNotExistErrCode                = 15
	DailyLimitReachedErrCode          = 17
	QPSLimitReachedErrCode            = 18
	TotalRequestLimitReachedErrCode   = 19
	InvalidRequestErrCode             = 100
	APITokenInvalidErrCode            = 110
	APITokenExpiredErrCode            = 111
	InternalErrorErrCode              = 336000
	InvalidArgumentErrCode            = 336001
	InvalidJSONErrCode                = 336002
	InvalidParamErrCode               = 336003
	PermissionErrorErrCode            = 336004
	APINameNotExistErrCode            = 336005
	ServerHighLoadErrCode             = 336100
	InvalidHTTPMethodErrCode          = 336101
	InvalidArgumentSystemErrCode      = 336104
	InvalidArgumentUserSettingErrCode = 336105

	ConsoleInternalErrorErrCode = 500000
)
