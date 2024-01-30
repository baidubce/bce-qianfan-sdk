package qianfan

type Option func(*Options)
type Options struct {
	Model    *string
	Endpoint *string
}

// 用于模型类对象设置使用的模型
func WithModel(model string) Option {
	return func(options *Options) {
		options.Model = &model
	}
}

// 用于模型类对象设置使用的 endpoint
func WithEndpoint(endpoint string) Option {
	return func(options *Options) {
		options.Endpoint = &endpoint
	}
}

// 将多个 Option 转换成最终的 Options 对象
func makeOptions(options ...Option) *Options {
	option := Options{}
	for _, opt := range options {
		opt(&option)
	}
	return &option
}
