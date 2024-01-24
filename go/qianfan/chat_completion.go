package qianfan

import (
	"context"
	"fmt"
)

type ChatCompletionMessage struct {
	Role         string       `json:"role"`
	Content      string       `json:"content"`
	Name         string       `json:"name,omitempty"`
	FunctionCall FunctionCall `json:"function_call,omitempty"`
}

type ChatCompletion struct {
	BaseModel
}

type FunctionCall struct {
	Name      string `json:"name"`
	Arguments string `json:"arguments"`
	Thoughts  string `json:"thoughts,omitempty"`
}

type FunctionExample struct {
	Role         string       `json:"role"`
	Content      string       `json:"content"`
	Name         string       `json:"name,omitempty"`
	FunctionCall FunctionCall `json:"function_call,omitempty"`
}

type Function struct {
	Name        string            `json:"name"`
	Description string            `json:"description"`
	Parameters  any               `json:"parameters"`
	Responses   any               `json:"responses,omitempty"`
	Examples    []FunctionExample `json:"examples,omitempty"`
}

type ToolChoice struct {
	Type     string   `json:"type"`
	Function Function `json:"function"`
	Name     string   `json:"name"`
}

type ChatCompletionRequest struct {
	BaseRequestBody
	Messages        []ChatCompletionMessage `mapstructure:"messages"`
	Temperature     float64                 `mapstructure:"temperature,omitempty"`
	TopP            float64                 `mapstructure:"top_p,omitempty"`
	PenaltyScore    float64                 `mapstructure:"penalty_score,omitempty"`
	System          string                  `mapstructure:"system,omitempty"`
	Stop            []string                `mapstructure:"stop,omitempty"`
	DisableSearch   bool                    `mapstructure:"disable_search,omitempty"`
	EnableCitation  bool                    `mapstructure:"enable_citation,omitempty"`
	MaxOutputTokens int                     `mapstructure:"max_output_tokens,omitempty"`
	ResponseFormat  string                  `mapstructure:"response_format,omitempty"`
	UserID          string                  `mapstructure:"user_id,omitempty"`
	Functions       []Function              `mapstructure:"functions,omitempty"`
	ToolChoice      ToolChoice              `mapstructure:"tool_choice,omitempty"`
}

func (r *ChatCompletionRequest) toMap() (map[string]interface{}, error) {
	m, err := dumpToMap(r)
	if err != nil {
		return nil, err
	}
	return r.BaseRequestBody.union(m)
}

var ChatModelEndpoint = map[string]string{
	"ERNIE-Bot-turbo":              "/chat/eb-instant",
	"ERNIE-Bot":                    "/chat/completions",
	"ERNIE-Bot-4":                  "/chat/completions_pro",
	"ERNIE-Bot-8k":                 "/chat/ernie_bot_8k",
	"ERNIE-Speed":                  "/chat/eb_turbo_pro",
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

func ChatCompletionUserMessage(message string) ChatCompletionMessage {
	return ChatCompletionMessage{
		Role:    "user",
		Content: message,
	}
}

func ChatCompletionAssistantMessage(message string) ChatCompletionMessage {
	return ChatCompletionMessage{
		Role:    "assistant",
		Content: message,
	}
}

func newChatCompletion(model string, endpoint string, client *Client) *ChatCompletion {
	return &ChatCompletion{
		BaseModel{
			Model:    model,
			Endpoint: endpoint,
			Client:   client,
		},
	}
}

func (c *ChatCompletion) realEndpoint() (string, error) {
	url := c.config.BaseURL + ModelAPIPrefix
	if c.Model != "" {
		endpoint, ok := ChatModelEndpoint[c.Model]
		if !ok {
			return "", fmt.Errorf("model %s is not supported", c.Model)
		}
		url += endpoint
	} else {
		url += "/chat/" + c.Endpoint
	}
	return url, nil
}

func (c *ChatCompletion) Do(ctx context.Context, request *ChatCompletionRequest) (*ModelResponse, error) {
	url, err := c.realEndpoint()
	if err != nil {
		return nil, err
	}
	req, err := newRequest("POST", url, request)
	if err != nil {
		return nil, err
	}
	return sendRequest[ModelResponse, *ModelResponse](c.requestor, req)
}

func (c *ChatCompletion) DoStream(ctx context.Context, request *ChatCompletionRequest) (*Stream[ModelResponse, *ModelResponse], error) {
	url, err := c.realEndpoint()
	if err != nil {
		return nil, err
	}
	m, err := request.toMap()
	if err != nil {
		return nil, err
	}
	m["stream"] = true
	req, err := newRequestFromMap("POST", url, m)
	if err != nil {
		return nil, err
	}
	return sendStreamRequest[ModelResponse, *ModelResponse](c.requestor, req)
}
