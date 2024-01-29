package qianfan

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestEmbedding(t *testing.T) {
	embed := NewEmbedding()
	resp, err := embed.Do(context.Background(), &EmbeddingRequest{
		Input: []string{"hello1", "hello2"},
	})
	assert.NoError(t, err)
	assert.Equal(t, resp.RawResponse.StatusCode, 200)
	assert.Equal(t, len(resp.Data), 2)
	assert.NotEqual(t, len(resp.Data), 0)
	assert.Contains(t, resp.RawResponse.Request.URL.Path, EmbeddingEndpoint[DefaultEmbeddingModel])
	req, err := getRequestBody[EmbeddingRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, req.Input[0], "hello1")
	assert.Equal(t, req.Input[1], "hello2")
}
