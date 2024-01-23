package qianfan

import (
	"context"
	"encoding/json"
	"io"
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

type ModelAPIError struct {
	ErrorCode int    `json:"error_code"`
	ErrorMsg  string `json:"error_msg"`
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
	ModelAPIError
	QfResponse
}

type ModelResponseStream struct {
	stream *Stream
}

func (s *ModelResponseStream) Recv() (*ModelResponse, error) {
	// resp := &ModelResponse{}
	resp, err := s.stream.Recv()
	if err != nil {
		return nil, err
	}
	if resp == nil {
		return nil, io.EOF
	}
	response := &ModelResponse{QfResponse: *resp}
	err = json.Unmarshal(resp.Body, response)
	if err != nil {
		return nil, err
	}
	return response, nil
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

func (m *BaseModel) doStream(ctx context.Context, request *QfRequest) (*ModelResponseStream, error) {
	stream, err := m.requestor.ModelRequestStream(request)
	if err != nil {
		return nil, err
	}

	return &ModelResponseStream{
		stream: stream,
	}, nil
}
