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
	"io"
	"net/http"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/mitchellh/mapstructure"
	"github.com/stretchr/testify/assert"
)

func TestChatCompletion(t *testing.T) {
	for model, endpoint := range ChatModelEndpoint {
		chat := NewChatCompletion(WithModel(model))
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
}

func TestMain(m *testing.M) {
	os.Setenv("QIANFAN_BASE_URL", "http://127.0.0.1:8866")
	os.Setenv("QIANFAN_ACCESS_KEY", "test_access_key")
	os.Setenv("QIANFAN_SECRET_KEY", "test_secret_key")
	// authManager.GetAccessToken(GetConfig().AK, GetConfig().SK)
	authManager.tokenMap[credential{AK: GetConfig().AK, SK: GetConfig().SK}] = &accessToken{
		token:         "expired_token",
		lastUpateTime: time.Now().Add(time.Duration(-100) * time.Hour),
	}

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
