package qianfan

type BaseModel struct {
	Model    string
	Endpoint string
	*Requestor
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

type SearchResult struct {
	Index int    `json:"index"`
	URL   string `json:"url"`
	Title string `json:"title"`
}
type SearchInfo struct {
	SearchResults []SearchResult `json:"search_results"`
}

type ModelResponse struct {
	Id               string        `json:"id"`
	Object           string        `json:"object"`
	Created          int           `json:"created"`
	SentenceId       int           `json:"sentence_id"`
	IsEnd            bool          `json:"is_end"`
	IsTruncated      bool          `json:"is_truncated"`
	Result           string        `json:"result"`
	NeedClearHistory bool          `json:"need_clear_history"`
	Usage            ModelUsage    `json:"usage"`
	FunctionCall     *FunctionCall `json:"function_call"`
	BanRound         int           `json:"ban_round"`
	SearchInfo       *SearchInfo   `json:"search_info"`
	ModelAPIError
	baseResponse
}

type ModelResponseStream struct {
	*streamInternal
}

func (s *ModelResponseStream) Recv() (*ModelResponse, error) {
	var resp ModelResponse
	err := s.streamInternal.Recv(&resp)
	if err != nil {
		return nil, err
	}
	return &resp, nil
}
