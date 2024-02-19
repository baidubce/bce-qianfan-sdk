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

import (
	"strconv"
)

// 模型相关的结构体基类
type BaseModel struct {
	Model      string // 使用的模型名称
	Endpoint   string // 使用的模型服务地址
	*Requestor        // Requstor 作为基类
}

// 使用量信息
type ModelUsage struct {
	PromptTokens     int `json:"prompt_tokens"`     // 问题tokens数
	CompletionTokens int `json:"completion_tokens"` // 回答tokens数
	TotalTokens      int `json:"total_tokens"`      // tokens总数
}

type ModelAPIResponse interface {
	GetError() (int, string)
}

// API 错误信息
type ModelAPIError struct {
	ErrorCode int    `json:"error_code"` // 错误码
	ErrorMsg  string `json:"error_msg"`  // 错误消息
}

// 获取错误码和错误信息
func (e *ModelAPIError) GetError() (int, string) {
	return e.ErrorCode, e.ErrorMsg
}

// 获取错误码
func (e *ModelAPIError) GetErrorCode() string {
	return strconv.Itoa(e.ErrorCode)
}

// 搜索结果
type SearchResult struct {
	Index int    `json:"index"` // 序号
	URL   string `json:"url"`   // 搜索结果URL
	Title string `json:"title"` // 搜索结果标题
}

// 搜索结果列表
type SearchInfo struct {
	SearchResults []SearchResult `json:"search_results"` // 搜索结果列表
}

// 模型响应的结果
type ModelResponse struct {
	Id               string        `json:"id"`                 // 本轮对话的id
	Object           string        `json:"object"`             // 回包类型
	Created          int           `json:"created"`            // 时间戳
	SentenceId       int           `json:"sentence_id"`        // 表示当前子句的序号。只有在流式接口模式下会返回该字段
	IsEnd            bool          `json:"is_end"`             // 表示当前子句是否是最后一句。只有在流式接口模式下会返回该字段
	IsTruncated      bool          `json:"is_truncated"`       // 当前生成的结果是否被截断
	Result           string        `json:"result"`             // 	对话返回结果
	NeedClearHistory bool          `json:"need_clear_history"` // 表示用户输入是否存在安全风险，是否关闭当前会话，清理历史会话信息
	Usage            ModelUsage    `json:"usage"`              // token统计信息
	FunctionCall     *FunctionCall `json:"function_call"`      // 由模型生成的函数调用，包含函数名称，和调用参数
	BanRound         int           `json:"ban_round"`          // 当need_clear_history为true时，此字段会告知第几轮对话有敏感信息，如果是当前问题，ban_round=-1
	SearchInfo       *SearchInfo   `json:"search_info"`        // 搜索数据，当请求参数enable_citation为true并且触发搜索时，会返回该字段
	ModelAPIError                  // API 错误信息
	baseResponse                   // 通用的响应信息
}

// 用于获取ModelResponse流式结果的结构体
type ModelResponseStream struct {
	*streamInternal
}

// 获取ModelResponse流式结果
func (s *ModelResponseStream) Recv() (*ModelResponse, error) {
	var resp ModelResponse
	err := s.streamInternal.Recv(&resp)
	if err != nil {
		return nil, err
	}
	if err = checkResponseError(&resp); err != nil {
		return &resp, err
	}
	return &resp, nil
}

func checkResponseError(resp ModelAPIResponse) error {
	errCode, errMsg := resp.GetError()
	if errCode != 0 {
		return &APIError{Code: errCode, Msg: errMsg}
	}
	return nil
}
