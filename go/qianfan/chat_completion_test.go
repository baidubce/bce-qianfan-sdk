package qianfan

import (
	"context"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestChatCompletion(t *testing.T) {
	client, err := NewClientFromEnv()
	if err != nil {
		t.Fatal(err)
	}
	chat := client.ChatCompletion()
	resp, err := chat.Do(context.Background(), &ChatCompletionRequest{
		Messages: []ChatCompletionMessage{
			ChatCompletionUserMessage("上海有什么好吃的"),
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	assert.Equal(t, "ok", resp.Result)
}

func TestMain(m *testing.M) {
	// fmt.Println("TestMain")
	// os.Setenv("QIANFAN_BASE_URL", "http://127.0.0.1:8866")
	// os.Setenv("QIANFAN_ACCESS_KEY", "test_access_key")
	// os.Setenv("QIANFAN_SECRET_KEY", "test_secret_key")

	os.Exit(m.Run())
}
