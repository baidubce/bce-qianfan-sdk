package qianfan

import (
	"context"
	"fmt"
)

type EmbeddingV2 struct {
	BaseModel
}

type EmbeddingV2Request struct {
	BaseRequestBody `mapstructure:"-"`
	Model           string   `mapstructure:"model"`
	Input           []string `mapstructure:"input"` // 输入的文本列表
	User            string   `mapstructure:"user,omitempty"`
}

type EmbeddingV2Data struct {
	*EmbeddingData
}

type EmbeddingV2Response struct {
	baseResponse                        // 基础的响应字段
	Id           string                 `json:"id"`            // 请求的id
	Object       string                 `json:"object"`        // 回包类型，固定值“embedding_list”
	Created      int                    `json:"created"`       // 创建时间
	Usage        *ModelUsage            `json:"usage"`         // token统计信息
	Data         []EmbeddingV2Data      `json:"data"`          // 嵌入向量数据列表
	Error        *ChatCompletionV2Error `mapstructure:"error"` // 错误信息
}

func NewEmbeddingV2(optionList ...Option) *EmbeddingV2 {
	options := makeOptions(optionList...)
	return newEmbeddingV2(options)
}

func newEmbeddingV2(options *Options) *EmbeddingV2 {
	embedding := &EmbeddingV2{
		BaseModel{
			Model:     DefaultEmbeddingModel,
			Requestor: newRequestor(options),
		},
	}
	if options.Model != nil {
		embedding.Model = *options.Model
	}

	return embedding
}

func (c *EmbeddingV2) Do(ctx context.Context, request *EmbeddingV2Request) (*EmbeddingV2Response, error) {
	var resp *EmbeddingV2Response
	var err error
	runErr := runWithContext(ctx, func() {
		resp, err = c.do(ctx, request)
	})
	if runErr != nil {
		return nil, runErr
	}
	return resp, err
}

func (c *EmbeddingV2) do(ctx context.Context, request *EmbeddingV2Request) (*EmbeddingV2Response, error) {
	do := func() (*EmbeddingV2Response, error) {
		req, err := NewBearerTokenRequest("POST", EmbeddingV2API, request)
		if err != nil {
			return nil, err
		}
		resp := &EmbeddingV2Response{}

		err = c.Requestor.request(ctx, req, resp)
		if err != nil {
			return nil, err
		}

		if resp.Error != nil {
			return nil, fmt.Errorf(
				"code: %s, type: %s, message: %s",
				resp.Error.Code,
				resp.Error.Type,
				resp.Error.Message,
			)
		}

		return resp, nil
	}
	return do()
}

func (c *EmbeddingV2Response) GetErrorCode() string {
	return c.Error.Message
}
