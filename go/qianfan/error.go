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

import "fmt"

// 模型不被支持，请使用 `ModelList()` 获取支持的模型列表
type ModelNotSupportedError struct {
	Model string
}

func (e *ModelNotSupportedError) Error() string {
	return fmt.Sprintf("model `%s` is not supported, use `ModelList()` to acquire supported model list", e.Model)
}

// API 返回错误
type APIError struct {
	Code int
	Msg  string
}

func (e *APIError) Error() string {
	return fmt.Sprintf("api error, code: %d, msg: %s", e.Code, e.Msg)
}

// 鉴权所需信息不足，需确保 (AccessKey, SecretKey) 或 (AK, SK) 存在
type CredentialNotFoundError struct {
}

func (e *CredentialNotFoundError) Error() string {
	return "no enough credentails found. Please set AK and SK or AccessKey and SecretKey"
}

// SDK 内部错误，若遇到请联系我们
type InternalError struct {
	Msg string
}

func (e *InternalError) Error() string {
	return fmt.Sprintf("internal error: %s. there might be a bug in sdk. please contact us", e.Msg)
}

// 参数非法
type InvalidParamError struct {
	Msg string
}

func (e *InvalidParamError) Error() string {
	return fmt.Sprint("invalid param ", e.Msg)
}

// 内部使用，表示重试
type tryAgainError struct {
}

func (e *tryAgainError) Error() string {
	return "try again"
}
