package qianfan

import (
	"context"
	"fmt"
)

type ReRankerV2 struct {
	BaseModel
}

type ReRankerV2Request struct {
	BaseRequestBody `mapstructure:"-"`
	Query           string   `mapstructure:"query"`           //查询文本
	Documents       []string `mapstructure:"documents"`       //需要重排序的文本
	TopN            int      `mapstructure:"top_n,omitempty"` //返回的最相关文本的数量
	User            string   `mapstructure:"user,omitempty"`  //用户标识
	Model           string   `mapstructure:"model"`           //模型名称
}

type ReRankerV2Data struct {
	*ReRankerData
}

type ReRankerV2Response struct {
	baseResponse                        // 基础的响应字段
	Id           string                 `json:"id"`      // 请求的id
	Object       string                 `json:"object"`  // 回包类型，固定值“ReRanker_list”
	Created      int                    `json:"created"` // 创建时间
	Results      []ReRankerV2Data       `json:"results"` // 嵌入向量数据列表
	Usage        *ModelUsage            `json:"usage"`   // token统计信息
	Error        *ChatCompletionV2Error `json:"error"`   // 错误信息
}

func NewReRankerV2(optionList ...Option) *ReRankerV2 {
	options := makeOptions(optionList...)
	return newReRankerV2(options)
}

func newReRankerV2(options *Options) *ReRankerV2 {
	reRankerV2 := &ReRankerV2{
		BaseModel{
			Model:     DefaultReRankerV2Model,
			Requestor: newRequestor(options),
		},
	}
	if options.Model != nil {
		reRankerV2.Model = *options.Model
	}

	return reRankerV2
}

func (c *ReRankerV2) Do(ctx context.Context, request *ReRankerV2Request) (*ReRankerV2Response, error) {
	var resp *ReRankerV2Response
	var err error
	if request.TopN <= 0 {
		request.TopN = len(request.Documents)
	}
	runErr := runWithContext(ctx, func() {
		resp, err = c.do(ctx, request)
	})
	if runErr != nil {
		return nil, runErr
	}
	return resp, err
}

func (c *ReRankerV2) do(ctx context.Context, request *ReRankerV2Request) (*ReRankerV2Response, error) {
	do := func() (*ReRankerV2Response, error) {
		req, err := NewBearerTokenRequest("POST", ReRankerV2API, request)
		if err != nil {
			return nil, err
		}
		resp := &ReRankerV2Response{}

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

func (c *ReRankerV2Response) GetErrorCode() string {
	return c.Error.Message
}
