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

// 表示对话内容的结构体
type ChatCompletionMessage struct {
	Role         string        `json:"role"`                    // 角色，可选 "user", "assistant", "function"
	Content      string        `json:"content"`                 // 对话内容
	Name         string        `json:"name,omitempty"`          // message 作者
	FunctionCall *FunctionCall `json:"function_call,omitempty"` // 函数调用
}

// 用于 chat 类型模型的结构体
type ChatCompletion struct {
	BaseModel
}

// 函数调用的结构体
type FunctionCall struct {
	Name      string `json:"name"`               // 触发的function名
	Arguments string `json:"arguments"`          // 请求参数
	Thoughts  string `json:"thoughts,omitempty"` // 模型思考过程
}

// function调用的示例
type FunctionExample struct {
	Role         string        `json:"role"`                    // 角色，可选 "user", "assistant", "function"
	Content      string        `json:"content"`                 // 对话内容
	Name         string        `json:"name,omitempty"`          // message 作者
	FunctionCall *FunctionCall `json:"function_call,omitempty"` // 函数调用
}

// 表示函数的结构体
type Function struct {
	Name        string              `json:"name"`                // 函数名
	Description string              `json:"description"`         // 函数描述
	Parameters  any                 `json:"parameters"`          // 函数请求参数
	Responses   any                 `json:"responses,omitempty"` // 函数响应参数
	Examples    [][]FunctionExample `json:"examples,omitempty"`  // function调用的一些历史示例
}

// 可选的工具
type ToolChoice struct {
	Type     string    `json:"type"`     // 指定工具类型
	Function *Function `json:"function"` // 指定要使用的函数
	Name     string    `json:"name"`     // 指定要使用的函数名
}

// chat 模型的请求结构体
type ChatCompletionRequest struct {
	BaseRequestBody `mapstructure:"-"`
	Messages        []ChatCompletionMessage `mapstructure:"messages"`                    // 聊天上下文信息
	Temperature     float64                 `mapstructure:"temperature,omitempty"`       // 较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定，范围 (0, 1.0]，不能为0
	TopP            float64                 `mapstructure:"top_p,omitempty"`             // 影响输出文本的多样性，取值越大，生成文本的多样性越强。取值范围 [0, 1.0]
	PenaltyScore    float64                 `mapstructure:"penalty_score,omitempty"`     // 通过对已生成的token增加惩罚，减少重复生成的现象。说明：值越大表示惩罚越大，取值范围：[1.0, 2.0]
	System          string                  `mapstructure:"system,omitempty"`            // 模型人设，主要用于人设设定
	Stop            []string                `mapstructure:"stop,omitempty"`              // 生成停止标识，当模型生成结果以stop中某个元素结尾时，停止文本生成
	DisableSearch   bool                    `mapstructure:"disable_search,omitempty"`    // 是否强制关闭实时搜索功能
	EnableCitation  bool                    `mapstructure:"enable_citation,omitempty"`   // 是否开启上角标返回
	MaxOutputTokens int                     `mapstructure:"max_output_tokens,omitempty"` // 指定模型最大输出token数
	ResponseFormat  string                  `mapstructure:"response_format,omitempty"`   // 指定响应内容的格式
	UserID          string                  `mapstructure:"user_id,omitempty"`           // 表示最终用户的唯一标识符
	Functions       []Function              `mapstructure:"functions,omitempty"`         // 一个可触发函数的描述列表
	ToolChoice      *ToolChoice             `mapstructure:"tool_choice,omitempty"`       // 在函数调用场景下，提示大模型选择指定的函数
}

// 内置 chat 模型的 endpoint
var ChatModelEndpoint = map[string]string{
	"ERNIE-Bot-turbo":              "/chat/eb-instant",
	"ERNIE-Bot":                    "/chat/completions",
	"ERNIE-Bot-4":                  "/chat/completions_pro",
	"ERNIE-Bot-8k":                 "/chat/ernie_bot_8k",
	"ERNIE-3.5-4K-0205":            "/chat/ernie-3.5-4k-0205",
	"ERNIE-3.5-8K-0205":            "/chat/ernie-3.5-8k-0205",
	"ERNIE-Speed":                  "/chat/ernie_speed",
	"ERNIE-Bot-turbo-AI":           "/chat/ai_apaas",
	"EB-turbo-AppBuilder":          "/chat/ai_apaas",
	"BLOOMZ-7B":                    "/chat/bloomz_7b1",
	"Llama-2-7b-chat":              "/chat/llama_2_7b",
	"Llama-2-13b-chat":             "/chat/llama_2_13b",
	"Llama-2-70b-chat":             "/chat/llama_2_70b",
	"Qianfan-BLOOMZ-7B-compressed": "/chat/qianfan_bloomz_7b_compressed",
	"Qianfan-Chinese-Llama-2-7B":   "/chat/qianfan_chinese_llama_2_7b",
	"ChatGLM2-6B-32K":              "/chat/chatglm2_6b_32k",
	"AquilaChat-7B":                "/chat/aquilachat_7b",
	"XuanYuan-70B-Chat-4bit":       "/chat/xuanyuan_70b_chat",
	"Qianfan-Chinese-Llama-2-13B":  "/chat/qianfan_chinese_llama_2_13b",
	"ChatLaw":                      "/chat/chatlaw",
	"Yi-34B-Chat":                  "/chat/yi_34b_chat",
}

// 创建一个 User 的消息
func ChatCompletionUserMessage(message string) ChatCompletionMessage {
	return ChatCompletionMessage{
		Role:    "user",
		Content: message,
	}
}

// 创建一个 Assistant 的消息
func ChatCompletionAssistantMessage(message string) ChatCompletionMessage {
	return ChatCompletionMessage{
		Role:    "assistant",
		Content: message,
	}
}

// 内部根据 options 创建一个 ChatCompletion 对象
func newChatCompletion(options *Options) *ChatCompletion {
	chat := &ChatCompletion{
		BaseModel{
			Model:     DefaultChatCompletionModel,
			Endpoint:  "",
			Requestor: newRequestor(options),
		},
	}
	if options.Model != nil {
		chat.Model = *options.Model
	}
	if options.Endpoint != nil {
		chat.Endpoint = *options.Endpoint
	}
	return chat
}

// 将 endpoint 转换成完整的 url
func (c *ChatCompletion) realEndpoint() (string, error) {
	url := modelAPIPrefix
	if c.Endpoint == "" {
		endpoint, ok := ChatModelEndpoint[c.Model]
		if !ok {
			return "", &ModelNotSupportedError{Model: c.Model}
		}
		url += endpoint
	} else {
		url += "/chat/" + c.Endpoint
	}
	logger.Debugf("requesting endpoint: %s", url)
	return url, nil
}

// 发送 chat 请求
func (c *ChatCompletion) Do(ctx context.Context, request *ChatCompletionRequest) (*ModelResponse, error) {
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
func (c *ChatCompletion) Stream(ctx context.Context, request *ChatCompletionRequest) (*ModelResponseStream, error) {
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
	return newModelResponseStream(stream), nil
}

// chat 支持的模型列表
func (c *ChatCompletion) ModelList() []string {
	i := 0
	list := make([]string, len(ChatModelEndpoint))
	for k := range ChatModelEndpoint {
		list[i] = k
		i++
	}
	return list
}

// 创建一个 ChatCompletion 对象
//
//	chat := qianfan.NewChatCompletion()  // 默认使用 ERNIE-Bot-turbo 模型
//
//	// 可以通过 WithModel 指定模型
//	chat := qianfan.NewChatCompletion(
//	    qianfan.WithModel("ERNIE-Bot-4"),  // 支持的模型可以通过 chat.ModelList() 获取
//	)
//	// 或者通过 WithEndpoint 指定 endpoint
//	chat := qianfan.NewChatCompletion(
//	    qianfan.WithEndpoint("your_custom_endpoint"),
//	)
func NewChatCompletion(optionList ...Option) *ChatCompletion {
	options := makeOptions(optionList...)
	return newChatCompletion(options)
}
