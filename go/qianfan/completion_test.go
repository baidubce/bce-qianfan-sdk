package qianfan

import (
	"context"
	"fmt"
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
	chat := client.CompletionFromModel("ERNIE-Bot-turbo")
	resp, err := chat.DoStream(context.Background(), &CompletionRequest{
		Prompt:      "上海有什么好吃的",
		Temperature: 0.5,
	})
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Close()
	for {
		resp, err := resp.Recv()

		if err != nil {
			assert.Fail(t, "got err")
		}
		if resp.IsEnd {
			break
		}
		fmt.Printf(resp.Result)
	}
	// assert.Equal(t, "ok", resp.Result)
}
