package qianfan

import (
	"fmt"
)

type Client struct {
	config *Config
}

func NewClientFromEnv() (*Client, error) {
	config, err := loadConfigFromEnv()
	if err != nil {
		return nil, fmt.Errorf("failed to load config from env: %v", err)
	}
	return &Client{config: config}, nil
}

func (c *Client) ChatCompletion() *ChatCompletion {
	return newChatCompletion(DefaultChatCompletionModel, "", c.config)
}

func (c *Client) ChatCompletionFromModel(model string) *ChatCompletion {
	return newChatCompletion(model, "", c.config)
}

func (c *Client) ChatCompletionFromEndpoint(endpoint string) *ChatCompletion {
	return newChatCompletion("", endpoint, c.config)
}

func (c *Client) Completion() *Completion {
	return newCompletion(DefaultCompletionModel, "", c.config)
}

func (c *Client) CompletionFromModel(model string) *Completion {
	return newCompletion(model, "", c.config)
}

func (c *Client) CompletionFromEndpoint(endpoint string) *Completion {
	return newCompletion("", endpoint, c.config)
}

func (c *Client) Embedding() *Embedding {
	return newEmbedding(DefaultEmbeddingModel, "", c.config)
}

func (c *Client) EmbeddingFromModel(model string) *Embedding {
	return newEmbedding(model, "", c.config)
}

func (c *Client) EmbeddingFromEndpoint(endpoint string) *Embedding {
	return newEmbedding("", endpoint, c.config)
}
