package qianfan

import (
	"context"
	"fmt"
)

type CompletionRequest struct {
	BaseRequestBody
	Prompt string `mapstructure:"prompt"`
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

func (r *CompletionRequest) toMap() (map[string]interface{}, error) {
	m, err := dumpToMap(r)
	if err != nil {
		return nil, err
	}
	return r.BaseRequestBody.union(m)
}

type Completion struct {
	BaseModel
}

var CompletionModelEndpoint = map[string]string{
	"SQLCoder-7B": "/completions/sqlcoder_7b",
}

func newCompletion(model string, endpoint string, config *Config) *Completion {
	requetor := newRequestor(config)
	return &Completion{BaseModel{Model: model, Endpoint: endpoint, config: config, requestor: requetor}}
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

func (c *Completion) Do(ctx context.Context, request *CompletionRequest) (*ModelResponse, error) {
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

func (c *Completion) DoStream(ctx context.Context, request *CompletionRequest) (*ModelResponseStream, error) {
	url, err := c.realEndpoint()
	if err != nil {
		return nil, err
	}
	m, err := request.toMap()
	if err != nil {
		return nil, err
	}
	m["stream"] = true
	req, err := makeRequestFromMap("POST", url, m)
	if err != nil {
		return nil, err
	}
	return c.BaseModel.doStream(ctx, req)
}
