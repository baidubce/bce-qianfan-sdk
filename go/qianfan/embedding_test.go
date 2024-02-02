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
