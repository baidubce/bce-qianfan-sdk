package qianfan

import (
	"fmt"
)

type Client struct {
	Config    *Config
	requestor *Requestor
}

func NewClient(accessKey string, secretKey string) (*Client, error) {
	config, err := loadConfigFromEnv()
	if err != nil {
		return nil, fmt.Errorf("failed to load config from env: %v", err)
	}
	config.AccessKey = accessKey
	config.SecretKey = secretKey
	return NewClientFromConfig(config)
}

func NewClientFromEnv() (*Client, error) {
	config, err := loadConfigFromEnv()
	if err != nil {
		return nil, fmt.Errorf("failed to load config from env: %v", err)
	}
	return NewClientFromConfig(config)
}

func NewClientFromConfig(config *Config) (*Client, error) {
	return &Client{
		Config:    config,
		requestor: newRequestor(config),
	}, nil
}

func (c *Client) ChatCompletion() *ChatCompletion {
	return newChatCompletion(DefaultChatCompletionModel, "", c)
}

func (c *Client) ChatCompletionFromModel(model string) *ChatCompletion {
	return newChatCompletion(model, "", c)
}

func (c *Client) ChatCompletionFromEndpoint(endpoint string) *ChatCompletion {
	return newChatCompletion("", endpoint, c)
}

func (c *Client) Completion() *Completion {
	return newCompletion(DefaultCompletionModel, "", c)
}

func (c *Client) CompletionFromModel(model string) *Completion {
	return newCompletion(model, "", c)
}

func (c *Client) CompletionFromEndpoint(endpoint string) *Completion {
	return newCompletion("", endpoint, c)
}

func (c *Client) Embedding() *Embedding {
	return newEmbedding(DefaultEmbeddingModel, "", c)
}

func (c *Client) EmbeddingFromModel(model string) *Embedding {
	return newEmbedding(model, "", c)
}

func (c *Client) EmbeddingFromEndpoint(endpoint string) *Embedding {
	return newEmbedding("", endpoint, c)
}
