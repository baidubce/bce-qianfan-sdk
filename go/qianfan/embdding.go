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

func (r *EmbeddingRequest) WithExtra(extra map[string]interface{}) *EmbeddingRequest {
	r.Extra = extra
	return r
}

var EmbeddingEndpoint = map[string]string{
	"Embedding-V1": "/embeddings/embedding-v1",
	"bge-large-en": "/embeddings/bge_large_en",
	"bge-large-zh": "/embeddings/bge_large_zh",
	"tao-8k":       "/embeddings/tao_8k",
}

func newEmbedding(options *Options) *Embedding {
	embedding := &Embedding{
		BaseModel{
			Model:     DefaultEmbeddingModel,
			Endpoint:  "",
			Requestor: newRequestor(options),
		},
	}
	if options.Model != nil {
		embedding.Model = *options.Model
	}
	if options.Endpoint != nil {
		embedding.Endpoint = *options.Endpoint
	}
	return embedding
}

func (c *Embedding) realEndpoint() (string, error) {
	url := ModelAPIPrefix
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
	req, err := newModelRequest("POST", url, request)
	if err != nil {
		return nil, err
	}

	return sendRequest[EmbeddingResponse](c.Requestor, req)
}

func NewEmbedding(optionList ...Option) *Embedding {
	options := makeOptions(optionList...)
	return newEmbedding(options)
}
