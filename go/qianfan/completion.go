package qianfan

type CompletionRequest struct {
	Prompt string `json:"prompt"`
	//Functions []string `json:"functions"`
	Temperature     float64  `json:"temperature,omitempty"`
	TopP            float64  `json:"top_p,omitempty"`
	PenaltyScore    float64  `json:"penalty_score,omitempty"`
	System          string   `json:"system,omitempty"`
	Stop            []string `json:"stop,omitempty"`
	DisableSearch   bool     `json:"disable_search,omitempty"`
	EnableCitation  bool     `json:"enable_citation,omitempty"`
	MaxOutputTokens int      `json:"max_output_tokens,omitempty"`
	ResponseFormat  string   `json:"response_format,omitempty"`
	UserID          string   `json:"user_id,omitempty"`
	//ToolChoice string `json:"tool_choice,omitempty"`
}
