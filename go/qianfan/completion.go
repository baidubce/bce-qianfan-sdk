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

func (r CompletionRequest) WithExtra(extra map[string]interface{}) CompletionRequest {
	r.Extra = extra
	return r
}

type Completion struct {
	BaseModel
	chatWrapper *ChatCompletion
}

var CompletionModelEndpoint = map[string]string{
	"SQLCoder-7B":           "/completions/sqlcoder_7b",
	"CodeLlama-7b-Instruct": "/completions/codellama_7b_instruct",
}

func newCompletion(options *Options) *Completion {
	model, err := getOptionsVal[string](options, modelOptionKey)
	hasModel := err == nil
	endpoint, err := getOptionsVal[string](options, endpointOptionKey)
	hasEndpoint := err == nil
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
		_, ok := ChatModelEndpoint[*model]
		if ok {
			comp.chatWrapper = newChatCompletion(options)
		} else {
			comp.Model = *model
		}
	}
	if hasEndpoint {
		comp.Endpoint = *endpoint
	}
	return &comp
}

func (c *Completion) realEndpoint() (string, error) {
	url := ModelAPIPrefix
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

func (c *Completion) Do(ctx context.Context, request CompletionRequest) (*ModelResponse, error) {
	if c.chatWrapper != nil {
		return c.chatWrapper.Do(ctx, *convertCompletionReqToChatReq(&request))
	}
	url, err := c.realEndpoint()
	if err != nil {
		return nil, err
	}
	req, err := newModelRequest("POST", url, request)
	if err != nil {
		return nil, err
	}

	return sendRequest[ModelResponse](c.Requestor, req)
}

func (c *Completion) Stream(ctx context.Context, request CompletionRequest) (*Stream[ModelResponse, *ModelResponse], error) {
	if c.chatWrapper != nil {
		return c.chatWrapper.Stream(ctx, *convertCompletionReqToChatReq(&request))
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
	return sendStreamRequest[ModelResponse](c.Requestor, req)
}

func NewCompletion(optionList ...Option) *Completion {
	options := toOptions(optionList...)
	return newCompletion(options)
}
