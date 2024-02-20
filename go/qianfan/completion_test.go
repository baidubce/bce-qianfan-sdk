// Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package qianfan

import (
	"context"
	"fmt"
	"math/rand"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestCompletion(t *testing.T) {
	prompt := "hello"

	completion := NewCompletion()
	resp, err := completion.Do(
		context.Background(),
		&CompletionRequest{
			Prompt: prompt,
		},
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
	resp, err = completion.Do(
		context.Background(),
		&CompletionRequest{
			Prompt:      prompt,
			Temperature: 0.5,
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "completion")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, CompletionModelEndpoint["SQLCoder-7B"])
	assert.Contains(t, resp.Result, prompt)
	reqComp, err := getRequestBody[CompletionRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, reqComp.Prompt, prompt)
	assert.Equal(t, reqComp.Temperature, 0.5)

	completion = NewCompletion(WithEndpoint("endpoint111"))
	resp, err = completion.Do(
		context.Background(),
		&CompletionRequest{
			Prompt:      prompt,
			Temperature: 0.5,
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "completion")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "endpoint111")
	assert.Contains(t, resp.Result, prompt)
	reqComp, err = getRequestBody[CompletionRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, reqComp.Prompt, prompt)
	assert.Equal(t, reqComp.Temperature, 0.5)
}

func TestCompletionStream(t *testing.T) {

	modelList := []string{"ERNIE-Bot-turbo", "SQLCoder-7B"}
	prompt := "hello"
	for _, m := range modelList {
		comp := NewCompletion(
			WithModel(m),
		)
		resp, err := comp.Stream(
			context.Background(),
			&CompletionRequest{
				Prompt:      prompt,
				Temperature: 0.5,
			},
		)
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
			assert.Contains(t, resp.Result, prompt)
		}
		assert.Greater(t, turnCount, 1)
	}
	for _, endpoint := range testEndpointList {
		comp := NewCompletion(
			WithEndpoint(endpoint),
		)
		resp, err := comp.Stream(
			context.Background(),
			&CompletionRequest{
				Prompt:      prompt,
				Temperature: 0.5,
			},
		)
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
			assert.Contains(t, resp.Result, prompt)
			assert.Equal(t, resp.Object, "completion")
			assert.Contains(t, resp.RawResponse.Request.URL.Path, endpoint)
			assert.Contains(t, resp.Result, prompt)
			reqComp, err := getRequestBody[CompletionRequest](resp.RawResponse)
			assert.NoError(t, err)
			assert.Equal(t, reqComp.Prompt, prompt)
			assert.Equal(t, reqComp.Temperature, 0.5)
		}
		assert.Greater(t, turnCount, 1)
	}
}

func TestCompletionModelList(t *testing.T) {
	list := NewCompletion().ModelList()
	assert.Greater(t, len(list), 0)
}

func TestCompletionUnsupportedModel(t *testing.T) {
	comp := NewCompletion(WithModel("unsupported_model"))
	_, err := comp.Do(
		context.Background(),
		&CompletionRequest{
			Prompt: "hello",
		},
	)
	assert.Error(t, err)
	var target *ModelNotSupportedError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Model, "unsupported_model")
}

func TestCompletionAPIError(t *testing.T) {
	comp := NewCompletion(
		WithEndpoint(fmt.Sprintf("test_retry_%d", rand.Intn(100000))),
	)
	_, err := comp.Do(
		context.Background(),
		&CompletionRequest{
			Prompt: "",
		},
	)
	assert.Error(t, err)
	var target *APIError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Code, 336100)
}

func TestStreamCompletionAPIError(t *testing.T) {
	comp := NewCompletion(
		WithEndpoint(fmt.Sprintf("test_retry_%d", rand.Intn(100000))),
	)
	s, err := comp.Stream(
		context.Background(),
		&CompletionRequest{
			Prompt: "",
		},
	)
	assert.NoError(t, err)
	_, err = s.Recv()
	assert.Error(t, err)
}

func TestCompletionRetry(t *testing.T) {
	defer resetTestEnv()
	comp := NewCompletion(
		WithEndpoint(fmt.Sprintf("test_retry_%d", rand.Intn(100000))),
		WithLLMRetryCount(5),
	)
	resp, err := comp.Do(
		context.Background(),
		&CompletionRequest{
			Prompt: "",
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "completion")
}

func TestCompletionStreamRetry(t *testing.T) {
	GetConfig().LLMRetryCount = 5
	defer resetTestEnv()
	prompt := "promptprompt"
	comp := NewCompletion(
		WithEndpoint(fmt.Sprintf("test_retry_%d", rand.Intn(100000))),
	)
	stream, err := comp.Stream(
		context.Background(),
		&CompletionRequest{
			Prompt: prompt,
		},
	)
	assert.NoError(t, err)
	turnCount := 0
	for {
		resp, err := stream.Recv()
		assert.NoError(t, err)
		if resp.IsEnd {
			break
		}
		turnCount++
		assert.Contains(t, resp.Result, prompt)
	}
	assert.Greater(t, turnCount, 1)

	comp = NewCompletion(
		WithEndpoint(fmt.Sprintf("test_retry_%d", rand.Intn(100000))),
		WithLLMRetryCount(1),
	)
	stream, err = comp.Stream(
		context.Background(),
		&CompletionRequest{
			Prompt: prompt,
		},
	)
	assert.NoError(t, err)
	_, err = stream.Recv()
	assert.Error(t, err)
	var target *APIError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Code, ServerHighLoadErrCode)
}
