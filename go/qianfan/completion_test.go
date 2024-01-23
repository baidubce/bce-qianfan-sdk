package qianfan

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestCompletion(t *testing.T) {
	client, err := NewClientFromEnv()
	if err != nil {
		t.Fatal(err)
	}
	completion := client.Completion()
	resp, err := completion.Do(context.Background(), &CompletionRequest{
		Prompt: "hello",
	})
	if err != nil {
		t.Fatal(err)
	}
	assert.Equal(t, "ok", resp.Result)
}
