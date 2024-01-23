package qianfan

import (
	"context"
	"fmt"
	"testing"
)

func TestEmbedding(t *testing.T) {
	client, err := NewClientFromEnv()
	if err != nil {
		t.Fatal(err)
	}
	embed := client.Embedding()
	resp, err := embed.Do(context.Background(), &EmbeddingRequest{
		Input: []string{"hello"},
	})
	if err != nil {
		t.Fatal(err)
	}
	fmt.Printf(resp.Object)
	// assert.Equal(t, "ok", resp.Result)
}
