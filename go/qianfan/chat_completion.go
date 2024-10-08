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
	"unicode/utf8"
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
	"ERNIE-4.0-Turbo-8K":            "/chat/ernie-4.0-turbo-8k",
	"ERNIE-4.0-8K-Latest":           "/chat/ernie-4.0-8k-latest",
	"ERNIE-4.0-8K-0613":             "/chat/ernie-4.0-8k-0613",
	"ERNIE-3.5-8K-0613":             "/chat/ernie-3.5-8k-0613",
	"ERNIE-Bot-turbo":               "/chat/eb-instant",
	"ERNIE-Lite-8K-0922":            "/chat/eb-instant",
	"ERNIE-Lite-8K":                 "/chat/ernie-lite-8k",
	"ERNIE-Lite-8K-0308":            "/chat/ernie-lite-8k",
	"ERNIE-Lite-AppBuilder-8K-0614": "/chat/ai_apaas_lite",
	"ERNIE-Lite-Pro-8K":             "/chat/ernie-lite-pro-8k",
	"ERNIE-Lite-V":                  "/chat/ernie-lite-v",
	"ERNIE-3.5-8K":                  "/chat/completions",
	"ERNIE-Bot":                     "/chat/completions",
	"ERNIE-4.0-8K":                  "/chat/completions_pro",
	"ERNIE-4.0-8K-Preview":          "/chat/ernie-4.0-8k-preview",
	"ERNIE-4.0-8K-Preview-0518":     "/chat/completions_adv_pro",
	"ERNIE-4.0-8K-0329":             "/chat/ernie-4.0-8k-0329",
	"ERNIE-4.0-8K-0104":             "/chat/ernie-4.0-8k-0104",
	"ERNIE-Bot-4":                   "/chat/completions_pro",
	"ERNIE-Bot-8k":                  "/chat/ernie_bot_8k",
	"ERNIE-3.5-128K":                "/chat/ernie-3.5-128k",
	"ERNIE-3.5-8K-preview":          "/chat/ernie-3.5-8k-preview",
	"ERNIE-3.5-8K-0329":             "/chat/ernie-3.5-8k-0329",
	"ERNIE-3.5-4K-0205":             "/chat/ernie-3.5-4k-0205",
	"ERNIE-3.5-8K-0205":             "/chat/ernie-3.5-8k-0205",
	"ERNIE-3.5-8K-0701":             "/chat/ernie-3.5-8k-0701",
	"ERNIE-3.5-8K-1222":             "/chat/ernie-3.5-8k-1222",
	"ERNIE Speed":                   "/chat/ernie_speed",
	"ERNIE-Speed":                   "/chat/ernie_speed",
	"ERNIE-Speed-8K":                "/chat/ernie_speed",
	"ERNIE-Speed-128K":              "/chat/ernie-speed-128k",
	"ERNIE Speed-AppBuilder":        "/chat/ai_apaas",
	"ERNIE-Speed-Pro-8K":            "/chat/ernie-speed-pro-8k",
	"ERNIE-Speed-Pro-128K":          "/chat/ernie-speed-pro-128k",
	"ERNIE-Tiny-8K":                 "/chat/ernie-tiny-8k",
	"ERNIE-Function-8K":             "/chat/ernie-func-8k",
	"ERNIE-Character-8K":            "/chat/ernie-char-8k",
	"ERNIE-Character-Fiction-8K":    "/chat/ernie-char-fiction-8k",
	"ERNIE-Bot-turbo-AI":            "/chat/ai_apaas",
	"ERNIE-Novel-8K":                "/chat/ernie-novel-8k",
	"EB-turbo-AppBuilder":           "/chat/ai_apaas",
	"BLOOMZ-7B":                     "/chat/bloomz_7b1",
	"Llama-2-7B-Chat":               "/chat/llama_2_7b",
	"Llama-2-13B-Chat":              "/chat/llama_2_13b",
	"Llama-2-70B-chat":              "/chat/llama_2_70b",
	"Qianfan-Chinese-Llama-2-7B":    "/chat/qianfan_chinese_llama_2_7b",
	"Qianfan-Chinese-Llama-2-13B":   "/chat/qianfan_chinese_llama_2_13b",
	"Qianfan-Chinese-Llama-2-70B":   "/chat/qianfan_chinese_llama_2_70b",
	"Meta-Llama-3-8B":               "/chat/llama_3_8b",
	"Meta-Llama-3-70B":              "/chat/llama_3_70b",
	"Qianfan-BLOOMZ-7B-compressed":  "/chat/qianfan_bloomz_7b_compressed",
	"ChatGLM2-6B-32K":               "/chat/chatglm2_6b_32k",
	"AquilaChat-7B":                 "/chat/aquilachat_7b",
	"XuanYuan-70B-Chat-4bit":        "/chat/xuanyuan_70b_chat",
	"ChatLaw":                       "/chat/chatlaw",
	"Yi-34B-Chat":                   "/chat/yi_34b_chat",
	"Mixtral-8x7B-Instruct":         "/chat/mixtral_8x7b_instruct",
	"Gemma-7B-it":                   "/chat/gemma_7b_it",
	"Qianfan-Dynamic-8K":            "/chat/qianfan-dynamic-8k",
}

// inputLimitInfo 结构体包含 maxInputChars 和 maxInputTokens
type inputLimitInfo struct {
	MaxInputChars  int
	MaxInputTokens int
}

// 定义包含所需信息的 map
var limitMapInModelName = map[string]inputLimitInfo{
	"ERNIE-4.0-Turbo-8K":            {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-4.0-8K-Latest":           {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-4.0-8K-0613":             {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-3.5-8K-0613":             {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-Lite-8K-0922":            {MaxInputChars: 11200, MaxInputTokens: 7168},
	"ERNIE-Lite-8K":                 {MaxInputChars: 11200, MaxInputTokens: 7168},
	"ERNIE-Lite-8K-0308":            {MaxInputChars: 11200, MaxInputTokens: 7168},
	"ERNIE-3.5-8K":                  {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-4.0-8K":                  {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-4.0-8K-0329":             {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-4.0-8K-0104":             {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-4.0-preemptible":         {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-4.0-8K-Preview-0518":     {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-4.0-8K-preview":          {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-3.5-8K-preemptible":      {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-3.5-128K":                {MaxInputChars: 516096, MaxInputTokens: 126976},
	"ERNIE-3.5-8K-preview":          {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-Bot-8K":                  {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-3.5-4K-0205":             {MaxInputChars: 8000, MaxInputTokens: 2048},
	"ERNIE-3.5-8K-0205":             {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-3.5-8K-1222":             {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-3.5-8K-0329":             {MaxInputChars: 8000, MaxInputTokens: 2048},
	"ERNIE-Speed-8K":                {MaxInputChars: 11200, MaxInputTokens: 7168},
	"ERNIE-Speed-128K":              {MaxInputChars: 507904, MaxInputTokens: 126976},
	"ERNIE Speed-AppBuilder":        {MaxInputChars: 11200, MaxInputTokens: 7168},
	"ERNIE-Tiny-8K":                 {MaxInputChars: 24000, MaxInputTokens: 6144},
	"ERNIE-Function-8K":             {MaxInputChars: 24000, MaxInputTokens: 6144},
	"ERNIE-Character-8K":            {MaxInputChars: 24000, MaxInputTokens: 6144},
	"ERNIE-Character-Fiction-8K":    {MaxInputChars: 24000, MaxInputTokens: 6144},
	"BLOOMZ-7B":                     {MaxInputChars: 4800, MaxInputTokens: 0},
	"Llama-2-7B-Chat":               {MaxInputChars: 4800, MaxInputTokens: 0},
	"Llama-2-13B-Chat":              {MaxInputChars: 4800, MaxInputTokens: 0},
	"Llama-2-70B-Chat":              {MaxInputChars: 4800, MaxInputTokens: 0},
	"Meta-Llama-3-8B":               {MaxInputChars: 4800, MaxInputTokens: 0},
	"Meta-Llama-3-70B":              {MaxInputChars: 4800, MaxInputTokens: 0},
	"Qianfan-BLOOMZ-7B-compressed":  {MaxInputChars: 4800, MaxInputTokens: 0},
	"Qianfan-Chinese-Llama-2-7B":    {MaxInputChars: 4800, MaxInputTokens: 0},
	"ChatGLM2-6B-32K":               {MaxInputChars: 4800, MaxInputTokens: 0},
	"AquilaChat-7B":                 {MaxInputChars: 4800, MaxInputTokens: 0},
	"XuanYuan-70B-Chat-4bit":        {MaxInputChars: 4800, MaxInputTokens: 0},
	"Qianfan-Chinese-Llama-2-13B":   {MaxInputChars: 4800, MaxInputTokens: 0},
	"Qianfan-Chinese-Llama-2-70B":   {MaxInputChars: 4800, MaxInputTokens: 0},
	"ChatLaw":                       {MaxInputChars: 4800, MaxInputTokens: 0},
	"Yi-34B-Chat":                   {MaxInputChars: 4800, MaxInputTokens: 0},
	"Mixtral-8x7B-Instruct":         {MaxInputChars: 4800, MaxInputTokens: 0},
	"Gemma-7B-it":                   {MaxInputChars: 4800, MaxInputTokens: 0},
	"UNSPECIFIED_MODEL":             {MaxInputChars: 0, MaxInputTokens: 0},
	"ERNIE-Lite-AppBuilder-8K-0614": {MaxInputChars: 11200, MaxInputTokens: 7168},
	"ERNIE-Lite-Pro-8K":             {MaxInputChars: 24000, MaxInputTokens: 6144},
	"ERNIE-Lite-V":                  {MaxInputChars: 24000, MaxInputTokens: 7168},
	"ERNIE-3.5-8K-0701":             {MaxInputChars: 20000, MaxInputTokens: 5120},
	"ERNIE-Speed-Pro-8K":            {MaxInputChars: 24000, MaxInputTokens: 6144},
	"ERNIE-Speed-Pro-128K":          {MaxInputChars: 516096, MaxInputTokens: 126976},
	"ERNIE-Novel-8K":                {MaxInputChars: 24000, MaxInputTokens: 6144},
	"Qianfan-Dynamic-8K":            {MaxInputChars: 20000, MaxInputTokens: 5120},
}

var limitMapInEndpoint = map[string]inputLimitInfo{
	"/chat/ernie-4.0-turbo-8k":           {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-4.0-8k-latest":          {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-4.0-8k-0613":            {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-3.5-8k-0613":            {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/eb-instant":                   {MaxInputChars: 11200, MaxInputTokens: 7168},
	"/chat/ernie-lite-8k":                {MaxInputChars: 11200, MaxInputTokens: 7168},
	"/chat/completions":                  {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/completions_pro":              {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-4.0-8k-0329":            {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-4.0-8k-0104":            {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/completions_pro_preemptible":  {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/completions_adv_pro":          {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-4.0-8k-preview":         {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/completions_preemptible":      {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-3.5-128k":               {MaxInputChars: 516096, MaxInputTokens: 126976},
	"/chat/ernie-3.5-8k-preview":         {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie_bot_8k":                 {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-3.5-4k-0205":            {MaxInputChars: 8000, MaxInputTokens: 2048},
	"/chat/ernie-3.5-8k-0205":            {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-3.5-8k-1222":            {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-3.5-8k-0329":            {MaxInputChars: 8000, MaxInputTokens: 2048},
	"/chat/ernie_speed":                  {MaxInputChars: 11200, MaxInputTokens: 7168},
	"/chat/ernie-speed-128k":             {MaxInputChars: 507904, MaxInputTokens: 126976},
	"/chat/ai_apaas":                     {MaxInputChars: 11200, MaxInputTokens: 7168},
	"/chat/ernie-tiny-8k":                {MaxInputChars: 24000, MaxInputTokens: 6144},
	"/chat/ernie-func-8k":                {MaxInputChars: 24000, MaxInputTokens: 6144},
	"/chat/ernie-char-8k":                {MaxInputChars: 24000, MaxInputTokens: 6144},
	"/chat/ernie-char-fiction-8k":        {MaxInputChars: 24000, MaxInputTokens: 6144},
	"/chat/bloomz_7b1":                   {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/llama_2_7b":                   {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/llama_2_13b":                  {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/llama_2_70b":                  {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/llama_3_8b":                   {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/llama_3_70b":                  {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/qianfan_bloomz_7b_compressed": {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/qianfan_chinese_llama_2_7b":   {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/chatglm2_6b_32k":              {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/aquilachat_7b":                {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/xuanyuan_70b_chat":            {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/qianfan_chinese_llama_2_13b":  {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/qianfan_chinese_llama_2_70b":  {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/chatlaw":                      {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/yi_34b_chat":                  {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/mixtral_8x7b_instruct":        {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/gemma_7b_it":                  {MaxInputChars: 4800, MaxInputTokens: 0},
	"/chat/ai_apaas_lite":                {MaxInputChars: 11200, MaxInputTokens: 7168},
	"/chat/ernie-lite-pro-8k":            {MaxInputChars: 24000, MaxInputTokens: 6144},
	"/chat/ernie-lite-v":                 {MaxInputChars: 24000, MaxInputTokens: 7168},
	"/chat/ernie-3.5-8k-0701":            {MaxInputChars: 20000, MaxInputTokens: 5120},
	"/chat/ernie-speed-pro-8k":           {MaxInputChars: 24000, MaxInputTokens: 6144},
	"/chat/ernie-speed-pro-128k":         {MaxInputChars: 516096, MaxInputTokens: 126976},
	"/chat/ernie-novel-8k":               {MaxInputChars: 24000, MaxInputTokens: 6144},
	"/chat/qianfan_dynamic_8k":           {MaxInputChars: 20000, MaxInputTokens: 5120},
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
func (c *ChatCompletion) realEndpoint(ctx context.Context) (string, error) {
	url := modelAPIPrefix
	if c.Endpoint == "" {
		endpoint := getModelEndpointRetriever().GetEndpoint(ctx, "chat", c.Model)
		if endpoint == "" {
			endpoint = getModelEndpointRetriever().GetEndpointWithRefresh(ctx, "chat", c.Model)
			if endpoint == "" {
				return "", &ModelNotSupportedError{Model: c.Model}
			}
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
	var resp *ModelResponse
	var err error
	runErr := runWithContext(ctx, func() {
		resp, err = c.do(ctx, request)
	})
	if runErr != nil {
		return nil, runErr
	}
	return resp, err
}

func (c *ChatCompletion) do(ctx context.Context, request *ChatCompletionRequest) (*ModelResponse, error) {
	do := func() (*ModelResponse, error) {
		url, err := c.realEndpoint(ctx)
		if err != nil {
			return nil, err
		}

		c.processWithInputLimit(ctx, request, url)

		req, err := NewModelRequest("POST", url, request)
		if err != nil {
			return nil, err
		}
		var resp ModelResponse

		err = c.requestResource(ctx, req, &resp)
		if err != nil {
			return nil, err
		}

		return &resp, nil
	}
	resp, err := do()
	if err != nil {
		if c.Endpoint == "" && isUnsupportedModelError(err) {
			// 根据 model 获得的 endpoint 错误，刷新模型列表后重试
			refreshErr := getModelEndpointRetriever().Refresh(ctx)
			if refreshErr != nil {
				logger.Errorf("refresh endpoint failed: %s", refreshErr)
				return resp, err
			}
			return do()
		}
		return resp, err
	}
	return resp, err
}

// 发送流式请求
func (c *ChatCompletion) Stream(ctx context.Context, request *ChatCompletionRequest) (*ModelResponseStream, error) {
	var resp *ModelResponseStream
	var err error
	runErr := runWithContext(ctx, func() {
		resp, err = c.stream(ctx, request)
	})
	if runErr != nil {
		return nil, runErr
	}
	return resp, err
}

func (c *ChatCompletion) stream(ctx context.Context, request *ChatCompletionRequest) (*ModelResponseStream, error) {
	do := func() (*ModelResponseStream, error) {
		url, err := c.realEndpoint(ctx)
		if err != nil {
			return nil, err
		}

		c.processWithInputLimit(ctx, request, url)

		request.SetStream()
		req, err := NewModelRequest("POST", url, request)
		if err != nil {
			return nil, err
		}
		stream, err := c.Requestor.requestStream(ctx, req)
		if err != nil {
			return nil, err
		}
		return newModelResponseStream(stream)
	}
	resp, err := do()
	if err != nil {
		if c.Endpoint == "" && isUnsupportedModelError(err) {
			refreshErr := getModelEndpointRetriever().Refresh(ctx)
			if refreshErr != nil {
				logger.Errorf("refresh endpoint failed: %s", refreshErr)
				return resp, err
			}
			return do()
		}
		return resp, err
	}
	return resp, err
}

func (c *ChatCompletion) processWithInputLimit(ctx context.Context, request *ChatCompletionRequest, url string) {
	if len(request.Messages) == 0 {
		return
	}

	url = url[len(modelAPIPrefix):]
	limit, ok := limitMapInEndpoint[url]
	if !ok {
		limit, ok = limitMapInModelName[c.Model]
		if !ok {
			limit = limitMapInModelName["UNSPECIFIED_MODEL"]
		}
	}

	if limit.MaxInputTokens == 0 && limit.MaxInputChars == 0 {
		return
	}

	messages := request.Messages
	totalMessageChars := 0
	totalMessageTokens := 0

	tokenizer := NewTokenizer()
	additionalArguments := make(map[string]interface{})

	truncatedIndex := len(messages) - 1

	for truncatedIndex > 0 {
		tokens, _ := tokenizer.CountTokens(messages[truncatedIndex].Content, TokenizerModeLocal, "", additionalArguments)

		totalMessageChars += utf8.RuneCountInString(messages[truncatedIndex].Content)
		totalMessageTokens += tokens

		if (limit.MaxInputTokens > 0 && totalMessageTokens > limit.MaxInputTokens) ||
			(limit.MaxInputChars > 0 && totalMessageChars > limit.MaxInputChars) {
			break
		}

		truncatedIndex--
	}

	request.Messages = request.Messages[truncatedIndex:]
}

// chat 支持的模型列表
func (c *ChatCompletion) ModelList() []string {
	i := 0
	models := getModelEndpointRetriever().GetModelList(context.TODO(), "chat")
	list := make([]string, len(models))
	for k := range models {
		list[i] = k
		i++
	}
	return list
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
func NewChatCompletion(optionList ...Option) *ChatCompletion {
	options := makeOptions(optionList...)
	return newChatCompletion(options)
}
