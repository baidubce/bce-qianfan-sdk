package qianfan

type Option func(*RequestorOptions)
type RequestorOptions struct {
	Model    *string
	Endpoint *string
}

func WithModel(model string) Option {
	return func(options *RequestorOptions) {
		options.Model = &model
	}
}

func WithEndpoint(endpoint string) Option {
	return func(options *RequestorOptions) {
		options.Endpoint = &endpoint
	}
}

func makeOptions(options ...Option) *RequestorOptions {
	option := RequestorOptions{}
	for _, opt := range options {
		opt(&option)
	}
	return &option
}
