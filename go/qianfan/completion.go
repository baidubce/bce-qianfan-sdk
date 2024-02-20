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
	"context"
)

// Completion 模型请求的参数结构体，但并非每个模型都完整支持如下参数，具体是否支持以 API 文档为准
type CompletionRequest struct {
	BaseRequestBody
	Prompt          string   `mapstructure:"prompt"`                      // 请求信息
	Temperature     float64  `mapstructure:"temperature,omitempty"`       // 较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定，范围 (0, 1.0]，不能为0
	TopK            int      `mapstructure:"top_k,omitempty"`             // Top-K 采样参数，在每轮token生成时，保留k个概率最高的token作为候选
	TopP            float64  `mapstructure:"top_p,omitempty"`             // 影响输出文本的多样性，取值越大，生成文本的多样性越强。取值范围 [0, 1.0]
	PenaltyScore    float64  `mapstructure:"penalty_score,omitempty"`     // 通过对已生成的token增加惩罚，减少重复生成的现象。说明：值越大表示惩罚越大，取值范围：[1.0, 2.0]
	System          string   `mapstructure:"system,omitempty"`            // 模型人设，主要用于人设设定
	Stop            []string `mapstructure:"stop,omitempty"`              // 生成停止标识，当模型生成结果以stop中某个元素结尾时，停止文本生成
	DisableSearch   bool     `mapstructure:"disable_search,omitempty"`    // 是否强制关闭实时搜索功能
	EnableCitation  bool     `mapstructure:"enable_citation,omitempty"`   // 是否开启上角标返回
	MaxOutputTokens int      `mapstructure:"max_output_tokens,omitempty"` // 指定模型最大输出token数
	ResponseFormat  string   `mapstructure:"response_format,omitempty"`   // 指定响应内容的格式
	UserID          string   `mapstructure:"user_id,omitempty"`           // 表示最终用户的唯一标识符
}

// 用于 Completion 模型请求的结构体
type Completion struct {
	BaseModel
	chatWrapper *ChatCompletion
}

// 内置 Completion 模型的 endpoint
var CompletionModelEndpoint = map[string]string{
	"SQLCoder-7B":           "/completions/sqlcoder_7b",
	"CodeLlama-7b-Instruct": "/completions/codellama_7b_instruct",
}

// 内部根据 Options 创建 Completion 对象
func newCompletion(options *Options) *Completion {
	hasModel := options.Model != nil
	hasEndpoint := options.Endpoint != nil
	comp := Completion{
		BaseModel: BaseModel{
			Model:     DefaultCompletionModel,
			Endpoint:  "",
			Requestor: newRequestor(options),
		},
		chatWrapper: nil,
	}
	// 如果 model 和 endpoint 都没提供，那就用 chatWrapper 默认值
	if !hasModel && !hasEndpoint {
		comp.chatWrapper = newChatCompletion(options)
	}
	// 如果提供了 model
	if hasModel {
		// 那就看模型是否是 chat 模型，如果是，就使用 chatWrapper
		_, ok := ChatModelEndpoint[*options.Model]
		if ok {
			comp.chatWrapper = newChatCompletion(options)
		} else {
			comp.Model = *options.Model
		}
	}
	if hasEndpoint {
		comp.Endpoint = *options.Endpoint
	}
	return &comp
}

// 将 endpoint 转换成完整的 endpoint
func (c *Completion) realEndpoint() (string, error) {
	url := modelAPIPrefix
	if c.Endpoint == "" {
		endpoint, ok := CompletionModelEndpoint[c.Model]
		if !ok {
			return "", &ModelNotSupportedError{Model: c.Model}
		}
		url += endpoint
	} else {
		url += "/completions/" + c.Endpoint
	}
	logger.Debugf("requesting endpoint: %s", url)
	return url, nil
}

// 将 completion 的请求转换为 chat 的请求
func convertCompletionReqToChatReq(request *CompletionRequest) *ChatCompletionRequest {
	chatReq := ChatCompletionRequest{
		BaseRequestBody: request.BaseRequestBody,
		Messages: []ChatCompletionMessage{
			ChatCompletionUserMessage(request.Prompt),
		},
		Temperature:     request.Temperature,
		TopP:            request.TopP,
		PenaltyScore:    request.PenaltyScore,
		System:          request.System,
		Stop:            request.Stop,
		DisableSearch:   request.DisableSearch,
		EnableCitation:  request.EnableCitation,
		MaxOutputTokens: request.MaxOutputTokens,
		ResponseFormat:  request.ResponseFormat,
		UserID:          request.UserID,
	}
	return &chatReq
}

// 发送请求
func (c *Completion) Do(ctx context.Context, request *CompletionRequest) (*ModelResponse, error) {
	if c.chatWrapper != nil {
		return c.chatWrapper.Do(ctx, convertCompletionReqToChatReq(request))
	}
	url, err := c.realEndpoint()
	if err != nil {
		return nil, err
	}
	req, err := newModelRequest("POST", url, request)
	if err != nil {
		return nil, err
	}
	var resp ModelResponse
	err = c.requestResource(req, &resp)
	if err != nil {
		return nil, err
	}

	return &resp, nil
}

// 发送流式请求
func (c *Completion) Stream(ctx context.Context, request *CompletionRequest) (*ModelResponseStream, error) {
	if c.chatWrapper != nil {
		return c.chatWrapper.Stream(ctx, convertCompletionReqToChatReq(request))
	}
	url, err := c.realEndpoint()
	if err != nil {
		return nil, err
	}
	request.SetStream()
	req, err := newModelRequest("POST", url, request)
	if err != nil {
		return nil, err
	}
	stream, err := c.Requestor.requestStream(req)
	if err != nil {
		return nil, err
	}
	return &ModelResponseStream{
		streamInternal: stream,
	}, nil
}

// 创建一个 Completion 实例
//
//	completion := qianfan.NewCompletion()  // 默认使用 ERNIE-Bot-turbo 模型
//
//	// 可以通过 WithModel 指定模型
//	completion := qianfan.NewCompletion(
//	    qianfan.WithModel("ERNIE-Bot-4"),
//	    // 支持的模型可以通过 completion.ModelList() 获取
//	)
//	// 或者通过 WithEndpoint 指定 endpoint
//	completion := qianfan.NewCompletion(
//	   qianfan.WithEndpoint("your_custom_endpoint"),
//	)
func NewCompletion(optionList ...Option) *Completion {
	options := makeOptions(optionList...)
	return newCompletion(options)
}

// Completion 支持的模型列表
func (c *Completion) ModelList() []string {
	i := 0
	list := make([]string, len(CompletionModelEndpoint))
	for k := range CompletionModelEndpoint {
		list[i] = k
		i++
	}
	list = append(list, (&ChatCompletion{}).ModelList()...)
	return list
}
