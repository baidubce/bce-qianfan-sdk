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
	"fmt"
)

// 用于 chat v2 类型模型的结构体
type ChatCompletionV2 struct {
	Model      string `mapstructure:"model"` // 模型ID
	*Requestor        // Requstor 作为基类
}

// chat 模型的请求结构体
type ChatCompletionV2Request struct {
	BaseRequestBody     `mapstructure:"-"`
	Model               string                    `mapstructure:"model"`                           // 模型ID
	Messages            []ChatCompletionV2Message `mapstructure:"messages"`                        // 聊天上下文信息
	StreamOptions       *StreamOptions            `mapstructure:"stream_options,omitempty"`        // 流式选项
	Temperature         float64                   `mapstructure:"temperature,omitempty"`           // 较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定，范围 (0, 1.0]，不能为0
	TopP                float64                   `mapstructure:"top_p,omitempty"`                 // 影响输出文本的多样性，取值越大，生成文本的多样性越强。取值范围 [0, 1.0]
	PenaltyScore        float64                   `mapstructure:"penalty_score,omitempty"`         // 通过对已生成的token增加惩罚，减少重复生成的现象。说明：值越大表示惩罚越大，取值范围：[1.0, 2.0]
	MaxCompletionTokens int                       `mapstructure:"max_completion_tokens,omitempty"` // 指定模型最大输出token数
	Seed                int                       `mapstructure:"seed,omitempty"`                  // 随机种子
	Stop                []string                  `mapstructure:"stop,omitempty"`                  // 生成停止标识，当模型生成结果以stop中某个元素结尾时，停止文本生成
	User                string                    `mapstructure:"user,omitempty"`                  // 表示最终用户的唯一标识符
	FrequencyPenalty    float64                   `mapstructure:"frequency_penalty,omitempty"`     // 指定频率惩罚，用于控制生成文本的重复程度。取值范围 [0.0,
	PresencePenalty     float64                   `mapstructure:"presence_penalty,omitempty"`      // 指定存在惩罚，用于控制生成文本的重复程度。
	Tools               []Tool                    `mapstructure:"tools,omitempty"`
	ToolChoice          any                       `mapstructure:"tool_choice,omitempty"`
	ParallelToolCalls   bool                      `mapstructure:"parallel_tool_calls,omitempty"` // 是否并行调用工具
	ResponseFormat      *ResponseFormat           `mapstructure:"response_format,omitempty"`
}

type ChatCompletionV2Response struct {
	baseResponse
	ID      string                   `mapstructure:"id"`      // 请求ID
	Object  string                   `mapstructure:"object"`  // 对象类型
	Created int64                    `mapstructure:"created"` // 创建时间
	Model   string                   `mapstructure:"model"`   // 模型ID
	Choices []ChatCompletionV2Choice `mapstructure:"choices"` // 生成结果
	Usage   *ModelUsage              `mapstructure:"usage"`   // 请求信息
	Error   *ChatCompletionV2Error   `mapstructure:"error"`   // 错误信息
}
type ChatCompletionV2Choice struct {
	Index        int                     `mapstructure:"index"`         // 生成结果索引
	Message      ChatCompletionV2Message `mapstructure:"message"`       // 生成结果
	Delta        ChatCompletionV2Delta   `mapstructure:"delta"`         // 生成结果
	FinishReason string                  `mapstructure:"finish_reason"` // 生成结果的分数
	Flag         int                     `mapstructure:"flag"`          // 生成结果的标志
	BanRound     int                     `mapstructure:"ban_round"`     // 生成结果
}

type ChatCompletionV2Message struct {
	Role       string     `mapstructure:"role" json:"role,omitempty"`
	Content    string     `mapstructure:"content,omitempty" json:"content,omitempty"`
	Name       string     `mapstructure:"name" json:"name,omitempty"`
	ToolCalls  []ToolCall `mapstructure:"tool_calls,omitempty" json:"tool_calls,omitempty"` // 函数调用
	ToolCallId string     `mapstructure:"tool_call_id,omitempty" json:"tool_call_id,omitempty"`
}

type ChatCompletionV2Delta struct {
	Content   string     `mapstructure:"content"`              // 生成结果
	ToolCalls []ToolCall `mapstructure:"tool_calls,omitempty"` // 函数调用
}

type StreamOptions struct {
	IncludeUsage bool `mapstructure:"include_usage,omitempty" json:"include_usage,omitempty"` //流式响应是否输出usage
}

type FunctionV2 struct {
	Name        string `mapstructure:"name" json:"name,omitempty"`
	Description string `mapstructure:"description" json:"description,omitempty"`
	Parameters  any    `mapstructure:"parameters" json:"parameters,omitempty"`
}

type FunctionCallV2 struct {
	Name      string `mapstructure:"name,omitempty" json:"name,omitempty"`
	Arguments string `mapstructure:"arguments,omitempty" json:"arguments,omitempty"`
}

type Tool struct {
	ToolType string     `mapstructure:"type" json:"type,omitempty"`
	Function FunctionV2 `mapstructure:"function" json:"function,omitempty"`
}

type ResponseFormat struct {
	FormatType string `mapstructure:"type" json:"type,omitempty"`
	JsonSchema any    `mapstructure:"json_schema" json:"json_schema,omitempty"`
}

type ToolCall struct {
	Id       string         `mapstructure:"id" json:"id,omitempty"`
	ToolType string         `mapstructure:"type" json:"type,omitempty"`
	Function FunctionCallV2 `mapstructure:"function" json:"function,omitempty"`
}

type ChatCompletionV2Error struct {
	Code    string `mapstructure:"code"`
	Message string `mapstructure:"message"`
	Type    string `mapstructure:"type"`
}

func (c *ChatCompletionV2Response) GetErrorCode() string {
	return c.Error.Message
}

type ChatCompletionV2ResponseStream struct {
	*streamInternal
}

// 内部根据 options 创建一个 ChatCompletion 对象
func newChatCompletionV2(options *Options) *ChatCompletionV2 {
	chat := &ChatCompletionV2{
		Requestor: newRequestor(options),
	}
	return chat
}

// 发送 chat 请求
func (c *ChatCompletionV2) Do(ctx context.Context, request *ChatCompletionV2Request) (*ChatCompletionV2Response, error) {
	var resp *ChatCompletionV2Response
	var err error
	runErr := runWithContext(ctx, func() {
		resp, err = c.do(ctx, request)
	})
	if runErr != nil {
		return nil, runErr
	}
	return resp, err
}

func (c *ChatCompletionV2) do(ctx context.Context, request *ChatCompletionV2Request) (*ChatCompletionV2Response, error) {
	do := func() (*ChatCompletionV2Response, error) {

		url := "/v2/chat/completions"

		req, err := NewBearerTokenRequest("POST", url, request)
		if err != nil {
			return nil, err
		}
		var resp ChatCompletionV2Response

		err = c.Requestor.request(ctx, req, &resp)

		if err != nil {
			return nil, err
		}

		if resp.Error != nil {
			return nil, fmt.Errorf(
				"code: %s, type: %s, message: %s",
				resp.Error.Code,
				resp.Error.Type,
				resp.Error.Message,
			)
		}

		return &resp, nil
	}
	resp, err := do()

	if err != nil {

		return resp, err
	}
	return resp, err
}

// 发送流式请求
func (c *ChatCompletionV2) Stream(ctx context.Context, request *ChatCompletionV2Request) (*ChatCompletionV2ResponseStream, error) {
	var resp *ChatCompletionV2ResponseStream
	var err error
	runErr := runWithContext(ctx, func() {
		resp, err = c.stream(ctx, request)
	})
	if runErr != nil {
		return nil, runErr
	}
	return resp, err
}

func newChatCompletionV2ResponseStream(si *streamInternal) (*ChatCompletionV2ResponseStream, error) {
	s := &ChatCompletionV2ResponseStream{streamInternal: si}
	return s, nil
}

func (c *ChatCompletionV2) stream(ctx context.Context, request *ChatCompletionV2Request) (*ChatCompletionV2ResponseStream, error) {
	do := func() (*ChatCompletionV2ResponseStream, error) {
		url := "/v2/chat/completions"

		request.SetStream()
		req, err := NewBearerTokenRequest("POST", url, request)
		if err != nil {
			return nil, err
		}
		stream, err := c.Requestor.requestStream(ctx, req)
		if err != nil {
			return nil, err
		}
		return newChatCompletionV2ResponseStream(stream)
	}
	resp, err := do()
	return resp, err
}

// 创建一个 ChatCompletion 对象
//
// chat := qianfan.NewChatCompletion()  // 使用默认模型
//
// 可以通过 WithModel 指定模型
// chat := qianfan.NewChatCompletion(
//
//	qianfan.WithModel("ERNIE-4.0-8K"),  // 支持的模型可以通过 chat.ModelList() 获取
//
// )
// 或者通过 WithEndpoint 指定 endpoint
// chat := qianfan.NewChatCompletion(
//
//	qianfan.WithEndpoint("your_custom_endpoint"),
//
// )
func NewChatCompletionV2(optionList ...Option) *ChatCompletionV2 {
	options := makeOptions(optionList...)
	return newChatCompletionV2(options)
}
