package qianfan

import (
	"context"
	"fmt"
)

type CompletionRequest struct {
	BaseRequestBody
	Prompt          string   `mapstructure:"prompt"`
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
}

func (r *CompletionRequest) toMap() (map[string]interface{}, error) {
	m, err := dumpToMap(r)
	if err != nil {
		return nil, err
	}
	return r.BaseRequestBody.union(m)
}

type Completion struct {
	BaseModel
	chatWrapper *ChatCompletion
}

var CompletionModelEndpoint = map[string]string{
	"SQLCoder-7B":           "/completions/sqlcoder_7b",
	"CodeLlama-7b-Instruct": "/completions/codellama_7b_instruct",
}

func newCompletion(model string, endpoint string, client *Client) *Completion {
	comp := Completion{
		BaseModel: BaseModel{
			Model:    model,
			Endpoint: endpoint,
			Client:   client,
		},
		chatWrapper: nil,
	}
	if model != "" {
		_, ok := ChatModelEndpoint[model]
		if ok {
			comp.chatWrapper = newChatCompletion(model, endpoint, client)
		}
	}
	return &comp
}

func (c *Completion) realEndpoint() (string, error) {
	url := c.Config.BaseURL + ModelAPIPrefix
	if c.Model != "" {
		endpoint, ok := CompletionModelEndpoint[c.Model]
		if !ok {
			return "", fmt.Errorf("model %s is not supported", c.Model)
		}
		url += endpoint
	} else {
		url += "/completions/" + c.Endpoint
	}
	return url, nil
}

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

func (c *Completion) Do(ctx context.Context, request *CompletionRequest) (*ModelResponse, error) {
	if c.chatWrapper != nil {
		return c.chatWrapper.Do(ctx, convertCompletionReqToChatReq(request))
	}
	url, err := c.realEndpoint()
	if err != nil {
		return nil, err
	}
	req, err := newRequest("POST", url, request)
	if err != nil {
		return nil, err
	}

	return sendRequest[ModelResponse](c.requestor, req)
}

func (c *Completion) DoStream(ctx context.Context, request *CompletionRequest) (*Stream[ModelResponse, *ModelResponse], error) {
	if c.chatWrapper != nil {
		return c.chatWrapper.DoStream(ctx, convertCompletionReqToChatReq(request))
	}
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
