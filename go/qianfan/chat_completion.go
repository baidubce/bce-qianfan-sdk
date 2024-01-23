package qianfan

import (
	"context"
	"fmt"
)

type ChatCompletionMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatCompletion struct {
	BaseModel
}

type ChatCompletionRequest struct {
	BaseRequestBody
	Messages []ChatCompletionMessage `mapstructure:"messages"`
	//Functions []string `json:"functions"`
	Temperature     float64  `mapstructure:"temperature,omitempty"`
	TopP            float64  `mapstructure:"top_p,omitempty"`
	PenaltyScore    float64  `mapstructure:"penalty_score,omitempty"`
	System          string   `mapstructure:"system,omitempty"`
	Stop            []string `mapstructure:"stop,omitempty"`
	DisableSearch   bool     `mapstructure:"disable_search,omitempty"`
	EnableCitation  bool     `mapstructure:"enable_citation,omitempty"`
	MaxOutputTokens int      `mapstructure:"max_output_tokens,omitempty"`
	ResponseFormat  string   `mapstructure:"response_format,omitempty"`
	UserID          string   `mapstructure:"user_id,omitempty"`
	//ToolChoice string `json:"tool_choice,omitempty"`
}

func (r *ChatCompletionRequest) toMap() (map[string]interface{}, error) {
	m, err := dumpToMap(r)
	if err != nil {
		return nil, err
	}
	return r.BaseRequestBody.union(m)
}

var ChatModelEndpoint = map[string]string{
	"ERNIE-Bot-turbo": "/chat/eb-instant",
	"ERNIE-Bot":       "/chat/completions",
	"ERNIE-Bot-4":     "/chat/completions_pro",
	"ERNIE-Bot-8k":    "/chat/ernie_bot_8k",
	"ERNIE-Speed":     "/chat/eb_turbo_pro",
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

func newChatCompletion(model string, endpoint string, config *Config) *ChatCompletion {
	requestor := newRequestor(config)
	return &ChatCompletion{BaseModel{Model: model, Endpoint: endpoint, config: config, requestor: requestor}}
}

func (c *ChatCompletion) realEndpoint() (string, error) {
	url := ModelAPIPrefix
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
	req, err := makeRequest("POST", url, request)
	if err != nil {
		return nil, err
	}
	return c.BaseModel.do(ctx, req)
}
