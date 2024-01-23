package qianfan

import (
	"context"
	"errors"
	"fmt"
	"io"
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
	fmt.Printf(resp.Result)
	// assert.Equal(t, "ok", resp.Result)
}
func TestCompletionStream(t *testing.T) {
	client, err := NewClientFromEnv()
	if err != nil {
		t.Fatal(err)
	}
	chat := client.Completion()
	resp, err := chat.DoStream(context.Background(), &CompletionRequest{
		Prompt: "hello",
	})
	if err != nil {
		t.Fatal(err)
	}
	defer resp.stream.Close()
	for {
		resp, err := resp.Recv()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			assert.Fail(t, "got err")
		}
		fmt.Printf(resp.Result)
	}
	// assert.Equal(t, "ok", resp.Result)
}
