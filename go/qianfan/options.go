package qianfan

import "fmt"

type Options map[string]interface{}
type Option func(*Options)

const (
	modelOptionKey    = "model"
	endpointOptionKey = "endpoint"
)

func WithModel(model string) Option {
	return func(options *Options) {
		(*options)[modelOptionKey] = model
	}
}

func WithEndpoint(endpoint string) Option {
	return func(options *Options) {
		(*options)[endpointOptionKey] = endpoint
	}
}

func toOptions(options ...Option) *Options {
	var result = make(Options)
	for _, option := range options {
		option(&result)
	}
	return &result
}

func getOptionsVal[T any](options *Options, key string) (*T, error) {
	if options == nil || len(*options) <= 0 {
		return nil, fmt.Errorf("options is nil")
	}

	val, ok := (*options)[key]
	if !ok {
		return nil, fmt.Errorf("options key %s not found", key)
	}
	switch t := val.(type) {
	case T:
		return &t, nil
	default:
		return nil, fmt.Errorf("options key %s type is not %T", key, t)
	}
}
