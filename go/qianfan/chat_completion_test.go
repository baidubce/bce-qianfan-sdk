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
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/mitchellh/mapstructure"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
)

var testEndpointList = []string{
	"endpoint1",
	"sidaofjnon",
	"98349823",
	"fjid_432",
}

func TestChatCompletion(t *testing.T) {
	for model, endpoint := range ChatModelEndpoint {
		chat := NewChatCompletion(WithModel(model))
		resp, err := chat.Do(
			context.Background(),
			&ChatCompletionRequest{
				Messages: []ChatCompletionMessage{
					ChatCompletionUserMessage("你好"),
					ChatCompletionAssistantMessage("回复"),
					ChatCompletionUserMessage("哈哈"),
				},
			},
		)
		assert.NoError(t, err)
		assert.Equal(t, resp.RawResponse.StatusCode, 200)
		assert.NotEqual(t, resp.Id, nil)
		assert.Equal(t, resp.Object, "chat.completion")
		assert.Contains(t, resp.RawResponse.Request.URL.Path, endpoint)
		assert.Contains(t, resp.Result, "你好")
		assert.Contains(t, resp.Result, "回复")
		assert.Contains(t, resp.Result, "哈哈")

		req, err := getRequestBody[ChatCompletionRequest](resp.RawResponse)
		assert.NoError(t, err)
		assert.Equal(t, req.Messages[0].Content, "你好")
	}
	for _, endpoint := range testEndpointList {
		chat := NewChatCompletion(WithEndpoint(endpoint))
		resp, err := chat.Do(
			context.Background(),
			&ChatCompletionRequest{
				Messages: []ChatCompletionMessage{
					ChatCompletionUserMessage("你好"),
				},
			},
		)
		assert.NoError(t, err)
		assert.Equal(t, resp.RawResponse.StatusCode, 200)
		assert.NotEqual(t, resp.Id, nil)
		assert.Equal(t, resp.Object, "chat.completion")
		assert.True(t, strings.Contains(resp.RawResponse.Request.URL.Path, endpoint))
		assert.True(t, strings.Contains(resp.Result, "你好"))

		req, err := getRequestBody[ChatCompletionRequest](resp.RawResponse)
		assert.NoError(t, err)
		assert.Equal(t, req.Messages[0].Content, "你好")
	}
}

func TestChatCompletionStream(t *testing.T) {
	for model, endpoint := range ChatModelEndpoint {
		chat := NewChatCompletion(WithModel(model))
		resp, err := chat.Stream(
			context.Background(),
			&ChatCompletionRequest{
				Messages: []ChatCompletionMessage{
					ChatCompletionUserMessage("你好"),
				},
			},
		)
		assert.NoError(t, err)
		turn_count := 0
		for {
			r, err := resp.Recv()
			assert.NoError(t, err)
			if resp.IsEnd {
				break
			}
			turn_count++
			assert.Equal(t, r.RawResponse.StatusCode, 200)
			assert.NotEqual(t, r.Id, nil)
			assert.Equal(t, r.Object, "chat.completion")
			assert.Contains(t, r.RawResponse.Request.URL.Path, endpoint)
			assert.Contains(t, r.Result, "你好")
			req, err := getRequestBody[ChatCompletionRequest](r.RawResponse)
			assert.NoError(t, err)
			assert.Equal(t, req.Messages[0].Content, "你好")
		}
		assert.True(t, turn_count > 1)
	}
	for _, endpoint := range testEndpointList {
		chat := NewChatCompletion(WithEndpoint(endpoint))
		resp, err := chat.Stream(
			context.Background(),
			&ChatCompletionRequest{
				Messages: []ChatCompletionMessage{
					ChatCompletionUserMessage("你好"),
				},
			},
		)
		assert.NoError(t, err)
		turn_count := 0
		for {
			r, err := resp.Recv()
			assert.NoError(t, err)
			if resp.IsEnd {
				break
			}
			turn_count++
			assert.Equal(t, r.RawResponse.StatusCode, 200)
			assert.NotEqual(t, r.Id, nil)
			assert.Equal(t, r.Object, "chat.completion")
			assert.Contains(t, r.RawResponse.Request.URL.Path, endpoint)
			assert.Contains(t, r.Result, "你好")
			req, err := getRequestBody[ChatCompletionRequest](r.RawResponse)
			assert.NoError(t, err)
			assert.Equal(t, req.Messages[0].Content, "你好")
		}
		assert.True(t, turn_count > 1)
	}
}

func TestChatCompletionUnsupportedModel(t *testing.T) {
	chat := NewChatCompletion(WithModel("unsupported_model"))
	_, err := chat.Do(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{
				ChatCompletionUserMessage("你好"),
			},
		},
	)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "unsupported_model")
	var target *ModelNotSupportedError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Model, "unsupported_model")
}

func TestChatCompletionAPIError(t *testing.T) {
	chat := NewChatCompletion()
	_, err := chat.Do(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{},
		},
	)
	assert.Error(t, err)
	var target *APIError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Code, 336003)
}

func TestChatCompletionModelList(t *testing.T) {
	list := NewChatCompletion().ModelList()
	assert.Greater(t, len(list), 0)
}

func TestChatCompletionRetry(t *testing.T) {
	defer resetTestEnv()
	chat := NewChatCompletion(
		WithEndpoint(fmt.Sprintf("test_retry_%d", rand.Intn(100000))),
		WithLLMRetryCount(5),
	)
	resp, err := chat.Do(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{
				ChatCompletionUserMessage("你好"),
			},
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "chat.completion")
	_, err = chat.Do(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{},
		},
	)
	var target *APIError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Code, InvalidParamErrCode)

	chat = NewChatCompletion(
		WithEndpoint(fmt.Sprintf("test_retry_%d", rand.Intn(100000))),
	)
	_, err = chat.Do(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{
				ChatCompletionUserMessage("你好"),
			},
		},
	)
	assert.Error(t, err)
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Code, ServerHighLoadErrCode)
}

func TestChatCompletionStreamRetry(t *testing.T) {
	GetConfig().LLMRetryCount = 5
	defer resetTestEnv()
	chat := NewChatCompletion(
		WithEndpoint(fmt.Sprintf("test_retry_%d", rand.Intn(100000))),
	)
	resp, err := chat.Stream(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{
				ChatCompletionUserMessage("你好"),
			},
		},
	)
	assert.NoError(t, err)
	turn_count := 0
	for {
		r, err := resp.Recv()
		assert.NoError(t, err)
		if resp.IsEnd {
			break
		}
		turn_count++
		assert.Equal(t, r.RawResponse.StatusCode, 200)
		assert.NotEqual(t, r.Id, nil)
		assert.Equal(t, r.Object, "chat.completion")
		assert.Contains(t, r.RawResponse.Request.URL.Path, "test_retry")
		assert.Contains(t, r.Result, "你好")
		req, err := getRequestBody[ChatCompletionRequest](r.RawResponse)
		assert.NoError(t, err)
		assert.Equal(t, req.Messages[0].Content, "你好")
	}
	assert.True(t, turn_count > 1)

	chat = NewChatCompletion(
		WithEndpoint(fmt.Sprintf("test_retry_%d", rand.Intn(100000))),
		WithLLMRetryCount(1),
	)
	resp, err = chat.Stream(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{
				ChatCompletionUserMessage("你好"),
			},
		},
	)
	assert.NoError(t, err)
	_, err = resp.Recv()
	assert.Error(t, err)
	var target *APIError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Code, ServerHighLoadErrCode)
}

func resetTestEnv() {
	rand.Seed(time.Now().UnixNano())
	logger.SetLevel(logrus.DebugLevel)
	os.Setenv("QIANFAN_BASE_URL", "http://127.0.0.1:8866")
	os.Setenv("QIANFAN_ACCESS_KEY", "test_access_key")
	os.Setenv("QIANFAN_SECRET_KEY", "test_secret_key")
	_authManager = nil
	_config = nil
}

func TestMain(m *testing.M) {
	resetTestEnv()

	os.Exit(m.Run())
}

func getRequestBody[T any](response *http.Response) (*T, error) {
	var body T
	rawBody, err := response.Request.GetBody()
	if err != nil {
		return nil, err
	}
	bodyBytes, err := io.ReadAll(rawBody)
	if err != nil {
		return nil, err
	}
	bodyMap := make(map[string]interface{})
	err = json.Unmarshal(bodyBytes, &bodyMap)
	if err != nil {
		return nil, err
	}
	err = mapstructure.Decode(bodyMap, &body)
	if err != nil {
		return nil, err
	}
	return &body, nil
}
