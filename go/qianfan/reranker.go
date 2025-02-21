package qianfan

import (
	"context"
)

type ReRanker struct {
	BaseModel
}

type ReRankerRequest struct {
	BaseRequestBody `mapstructure:"-"`
	Query           string   `mapstructure:"query"`             //查询文本
	Documents       []string `mapstructure:"documents"`         //需要重排序的文本
	TopN            int      `mapstructure:"top_n,omitempty"`   //返回的最相关文本的数量
	UserID          string   `mapstructure:"user_id,omitempty"` // 表示最终用户的唯一标识符
}
type ReRankerResponse struct {
	Id      string         `json:"id"`      //本轮对话的id
	Object  string         `json:"object"`  //回包类型
	Created int            `json:"created"` //创建时间
	Results []ReRankerData `json:"results"` //重排序结果，按相似性得分倒序
	Usage   ModelUsage     `json:"usage"`   // token统计信息
	ModelAPIError
	baseResponse
}

type ReRankerData struct {
	Document       string  `json:"document"`        //文档内容
	RelevanceScore float64 `json:"relevance_score"` //相似性得分
	Index          int     `json:"index"`           //排序
}

func NewReRanker(optionList ...Option) *ReRanker {
	options := makeOptions(optionList...)
	return newReRanker(options)
}

// 内部根据 options 创建 Embedding 实例
func newReRanker(options *Options) *ReRanker {
	reRanker := &ReRanker{
		BaseModel{
			Model:     DefaultReRankerModel,
			Endpoint:  "",
			Requestor: newRequestor(options),
		},
	}
	if options.Model != nil {
		reRanker.Model = *options.Model
	}
	if options.Endpoint != nil {
		reRanker.Endpoint = *options.Endpoint
	}
	return reRanker
}

var ReRankerEndpoint = map[string]string{
	"bce-reranker-base_v1": "/reranker/bce_reranker_base",
}

func (r *ReRanker) Do(ctx context.Context, request *ReRankerRequest) (*ReRankerResponse, error) {
	var resp *ReRankerResponse
	var err error

	if request.TopN <= 0 {
		request.TopN = len(request.Documents)
	}
	runErr := runWithContext(ctx, func() {
		resp, err = r.do(ctx, request)
	})
	if runErr != nil {
		return nil, runErr
	}
	return resp, err
}

func (r *ReRanker) do(ctx context.Context, request *ReRankerRequest) (*ReRankerResponse, error) {
	do := func() (*ReRankerResponse, error) {
		url, err := r.realEndpoint(ctx)
		if err != nil {
			return nil, err
		}
		req, err := NewModelRequest("POST", url, request)
		if err != nil {
			return nil, err
		}
		resp := &ReRankerResponse{}

		err = r.requestResource(ctx, req, resp)
		if err != nil {
			return nil, err
		}

		return resp, nil
	}
	resp, err := do()
	if err != nil {
		if r.Endpoint == "" && isUnsupportedModelError(err) {
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

// ModelList 获取 ReRanker 支持的模型列表
func (r *ReRanker) ModelList() []string {
	models := getModelEndpointRetriever().GetModelList(context.TODO(), "reranker")
	list := make([]string, len(models))
	i := 0
	for k := range EmbeddingEndpoint {
		list[i] = k
		i++
	}
	return list
}

func (r *ReRanker) realEndpoint(ctx context.Context) (string, error) {
	url := modelAPIPrefix
	if r.Endpoint == "" {
		endpoint := getModelEndpointRetriever().GetEndpoint(ctx, "reranker", r.Model)
		if endpoint == "" {
			endpoint = getModelEndpointRetriever().GetEndpointWithRefresh(ctx, "reranker", r.Model)
			if endpoint == "" {
				return "", &ModelNotSupportedError{Model: r.Model}
			}
		}
		url += endpoint
	} else {
		url += "/reranker/" + r.Endpoint
	}
	logger.Debugf("requesting endpoint: %s", url)
	return url, nil
}
