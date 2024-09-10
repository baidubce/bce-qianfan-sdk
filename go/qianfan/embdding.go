// Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package qianfan

import (
	"context"
)

// 用于 Embedding 相关操作的结构体
type Embedding struct {
	BaseModel
}

// Embedding 请求
type EmbeddingRequest struct {
	BaseRequestBody `mapstructure:"-"`
	Input           []string `mapstructure:"input"`             // 输入的文本列表
	UserID          string   `mapstructure:"user_id,omitempty"` // 表示最终用户的唯一标识符
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
func (c *Embedding) realEndpoint(ctx context.Context) (string, error) {
	url := modelAPIPrefix
	if c.Endpoint == "" {
		endpoint := getModelEndpointRetriever().GetEndpoint(ctx, "embeddings", c.Model)
		if endpoint == "" {
			endpoint = getModelEndpointRetriever().GetEndpointWithRefresh(ctx, "embeddings", c.Model)
			if endpoint == "" {
				return "", &ModelNotSupportedError{Model: c.Model}
			}
		}
		url += endpoint
	} else {
		url += "/embeddings/" + c.Endpoint
	}
	logger.Debugf("requesting endpoint: %s", url)
	return url, nil
}

// 发送 Embedding 请求
func (c *Embedding) Do(ctx context.Context, request *EmbeddingRequest) (*EmbeddingResponse, error) {
	var resp *EmbeddingResponse
	var err error
	runErr := runWithContext(ctx, func() {
		resp, err = c.do(ctx, request)
	})
	if runErr != nil {
		return nil, runErr
	}
	return resp, err
}

func (c *Embedding) do(ctx context.Context, request *EmbeddingRequest) (*EmbeddingResponse, error) {
	do := func() (*EmbeddingResponse, error) {
		url, err := c.realEndpoint(ctx)
		if err != nil {
			return nil, err
		}
		req, err := NewModelRequest("POST", url, request)
		if err != nil {
			return nil, err
		}
		resp := &EmbeddingResponse{}

		err = c.requestResource(ctx, req, resp)
		if err != nil {
			return nil, err
		}

		return resp, nil
	}
	resp, err := do()
	if err != nil {
		if c.Endpoint == "" && isUnsupportedModelError(err) {
			// 根据 model 获得的 endpoint 错误，刷新模型列表后重试
			refreshErr := getModelEndpointRetriever().Refresh(ctx)
			if refreshErr != nil {
				logger.Errorf("refresh endpoint failed: %s", refreshErr)
				return resp, err
			}
			return do()
		}
		return resp, err
	}
	return resp, err
}

// 获取 Embedding 支持的模型列表
func (c *Embedding) ModelList() []string {
	models := getModelEndpointRetriever().GetModelList(context.TODO(), "embeddings")
	list := make([]string, len(models))
	i := 0
	for k := range EmbeddingEndpoint {
		list[i] = k
		i++
	}
	return list
}
