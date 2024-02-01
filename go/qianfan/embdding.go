package qianfan

import (
	"context"
	"fmt"
)

// 用于 Embedding 相关操作的结构体
type Embedding struct {
	BaseModel
}

// Embedding 请求
type EmbeddingRequest struct {
	BaseRequestBody
	Input  []string `mapstructure:"input"`             // 输入的文本列表
	UserID string   `mapstructure:"user_id,omitempty"` // 表示最终用户的唯一标识符
}

// 具体的 Embedding 信息
type EmbeddingData struct {
	Object    string    `json:"object"`    // 固定值"embedding"
	Embedding []float64 `json:"embedding"` // embedding 内容
	Index     int       `json:"index"`     // 序号
}

// 返回的 Embedding 数据
type EmbeddingResponse struct {
	Id            string          `json:"id"`      // 请求的id
	Object        string          `json:"object"`  // 回包类型，固定值“embedding_list”
	Created       int             `json:"created"` // 创建时间
	Usage         ModelUsage      `json:"usage"`   // token统计信息
	Data          []EmbeddingData `json:"data"`    // embedding 数据
	ModelAPIError                 // API 错误信息
	baseResponse                  // 基础的响应字段
}

// 内置 Embedding 模型的 endpoint
var EmbeddingEndpoint = map[string]string{
	"Embedding-V1": "/embeddings/embedding-v1",
	"bge-large-en": "/embeddings/bge_large_en",
	"bge-large-zh": "/embeddings/bge_large_zh",
	"tao-8k":       "/embeddings/tao_8k",
}

// 创建 Embedding 实例
func NewEmbedding(optionList ...Option) *Embedding {
	options := makeOptions(optionList...)
	return newEmbedding(options)
}

// 内部根据 options 创建 Embedding 实例
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

// endpoint 转成完整 url
func (c *Embedding) realEndpoint() (string, error) {
	url := modelAPIPrefix
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

// 发送 Embedding 请求
func (c *Embedding) Do(ctx context.Context, request *EmbeddingRequest) (*EmbeddingResponse, error) {
	url, err := c.realEndpoint()
	if err != nil {
		return nil, err
	}
	req, err := newModelRequest("POST", url, request)
	if err != nil {
		return nil, err
	}
	resp := &EmbeddingResponse{}

	err = c.Requestor.request(req, resp)
	if err != nil {
		return nil, err
	}
	if err = checkResponseError(resp); err != nil {
		return resp, err
	}
	return resp, nil
}

// 获取 Embedding 支持的模型列表
func (c *Embedding) ModelList() []string {
	list := make([]string, len(EmbeddingEndpoint))
	i := 0
	for k := range EmbeddingEndpoint {
		list[i] = k
		i++
	}
	return list
}
