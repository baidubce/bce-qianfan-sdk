package qianfan

import (
	"context"
	"fmt"
)

type Embedding struct {
	BaseModel
}

type EmbeddingRequest struct {
	BaseRequestBody
	Input  []string `mapstructure:"input"`
	UserID string   `mapstructure:"user_id,omitempty"`
}

type EmbeddingData struct {
	Object    string    `json:"object"`
	Embedding []float64 `json:"embedding"`
	Index     int       `json:"index"`
}

type EmbeddingResponse struct {
	Id      string          `json:"id"`
	Object  string          `json:"object"`
	Created int             `json:"created"`
	Usage   ModelUsage      `json:"usage"`
	Data    []EmbeddingData `json:"data"`
	ModelAPIError
	baseResponse
}

func (r *EmbeddingRequest) toMap() (map[string]interface{}, error) {
	m, err := dumpToMap(r)
	if err != nil {
		return nil, err
	}
	return r.BaseRequestBody.union(m)
}

var EmbeddingEndpoint = map[string]string{
	"Embedding-V1": "/embeddings/embedding-v1",
	"bge-large-en": "/embeddings/bge_large_en",
	"bge-large-zh": "/embeddings/bge_large_zh",
	"tao-8k":       "/embeddings/tao_8k",
}

func newEmbedding(model string, endpoint string, client *Client) *Embedding {
	return &Embedding{
		BaseModel{
			Model:    model,
			Endpoint: endpoint,
			Client:   client,
		},
	}
}

func (c *Embedding) realEndpoint() (string, error) {
	url := c.Config.BaseURL + ModelAPIPrefix
	if c.Model != "" {
		endpoint, ok := EmbeddingEndpoint[c.Model]
		if !ok {
			return "", fmt.Errorf("model %s is not supported", c.Model)
		}
		url += endpoint
	} else {
		url += "/embeddings/" + c.Endpoint
	}
	return url, nil
}

func (c *Embedding) Do(ctx context.Context, request *EmbeddingRequest) (*EmbeddingResponse, error) {
	url, err := c.realEndpoint()
	if err != nil {
		return nil, err
	}
	req, err := newRequest("POST", url, request)
	if err != nil {
		return nil, err
	}

	return sendRequest[EmbeddingResponse, *EmbeddingResponse](c.requestor, req)
}
