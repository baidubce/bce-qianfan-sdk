package qianfan

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestCompletion(t *testing.T) {
	prompt := "hello"

	completion := NewCompletion()
	resp, err := completion.Do(
		context.Background(),
		CompletionRequest{
			Prompt: prompt,
		}.WithExtra(map[string]interface{}{}),
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.RawResponse.StatusCode, 200)
	assert.NotEqual(t, resp.Id, nil)
	assert.Equal(t, resp.Object, "chat.completion")
	assert.Contains(t,
		resp.RawResponse.Request.URL.Path,
		ChatModelEndpoint[DefaultCompletionModel],
	)
	assert.Contains(t, resp.Result, prompt)
	request, err := getRequestBody[ChatCompletionRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, request.Messages[0].Content, prompt)

	completion = NewCompletion(WithModel("SQLCoder-7B"))
	resp, err = completion.Do(context.Background(), CompletionRequest{
		Prompt:      prompt,
		Temperature: 0.5,
	})
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "completion")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, CompletionModelEndpoint["SQLCoder-7B"])
	assert.Contains(t, resp.Result, prompt)
	reqComp, err := getRequestBody[CompletionRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, reqComp.Prompt, prompt)
	assert.Equal(t, reqComp.Temperature, 0.5)
}

func TestCompletionStream(t *testing.T) {

	modelList := []string{"ERNIE-Bot-turbo", "SQLCoder-7B"}
	for _, m := range modelList {
		chat := NewCompletion(
			WithModel(m),
		)
		resp, err := chat.Stream(context.Background(), CompletionRequest{
			Prompt:      "hello",
			Temperature: 0.5,
		})
		assert.NoError(t, err)
		defer resp.Close()
		turnCount := 0
		for {
			resp, err := resp.Recv()
			assert.NoError(t, err)
			if resp.IsEnd {
				break
			}
			turnCount++
			assert.Contains(t, resp.Result, "hello")
		}
		assert.Greater(t, turnCount, 1)
	}
}
