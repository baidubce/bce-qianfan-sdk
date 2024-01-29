package qianfan

type Option func(*Options)
type Options struct {
	Model    *string
	Endpoint *string
}

func WithModel(model string) Option {
	return func(options *Options) {
		options.Model = &model
	}
}

func WithEndpoint(endpoint string) Option {
	return func(options *Options) {
		options.Endpoint = &endpoint
	}
}

func makeOptions(options ...Option) *Options {
	option := Options{}
	for _, opt := range options {
		opt(&option)
	}
	return &option
}
