package qianfan

import (
	"context"
	"encoding/json"
)

type BaseModel struct {
	Model     string
	Endpoint  string
	config    *Config
	requestor *Requestor
}

type ModelUsage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

type ModelResponse struct {
	Id               string     `json:"id"`
	Object           string     `json:"object"`
	Created          int        `json:"created"`
	SentenceId       int        `json:"sentence_id"`
	IsEnd            bool       `json:"is_end"`
	IsTruncated      bool       `json:"is_truncated"`
	Result           string     `json:"result"`
	NeedClearHistory bool       `json:"need_clear_history"`
	Usage            ModelUsage `json:"usage"`
	// FunctionCall     FunctionCall `json:"function_call"`
	BanRound int `json:"ban_round"`
	// SearchInfo      SearchInfo   `json:"search_info"`
	QfResponse
}

func (m *BaseModel) do(ctx context.Context, request *QfRequest) (*ModelResponse, error) {
	resp, err := m.requestor.ModelRequest(request)
	if err != nil {
		return nil, err
	}
	response := &ModelResponse{QfResponse: *resp}
	err = json.Unmarshal(resp.Body, response)
	if err != nil {
		return nil, err
	}
	return response, nil
}
