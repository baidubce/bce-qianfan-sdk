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
	"time"

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
	assert.Equal(t, len(req.Input), 2)

	embed = NewEmbedding(WithModel("bge-large-zh"))
	resp, err = embed.Do(context.Background(), &EmbeddingRequest{
		Input: []string{"hello3"},
	})
	assert.NoError(t, err)
	assert.Equal(t, resp.RawResponse.StatusCode, 200)
	assert.Equal(t, len(resp.Data), 1)
	assert.NotEqual(t, len(resp.Data), 0)
	assert.Contains(t, resp.RawResponse.Request.URL.Path, EmbeddingEndpoint["bge-large-zh"])
	req, err = getRequestBody[EmbeddingRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, req.Input[0], "hello3")
	assert.Equal(t, len(req.Input), 1)

	embed = NewEmbedding(WithEndpoint("custom_endpoint"))
	resp, err = embed.Do(context.Background(), &EmbeddingRequest{
		Input: []string{"hello4"},
	})
	assert.NoError(t, err)
	assert.Equal(t, resp.RawResponse.StatusCode, 200)
	assert.Equal(t, len(resp.Data), 1)
	assert.NotEqual(t, len(resp.Data), 0)
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "custom_endpoint")
	req, err = getRequestBody[EmbeddingRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, req.Input[0], "hello4")
	assert.Equal(t, len(req.Input), 1)
}

func TestEmbeddingModelList(t *testing.T) {
	embed := NewEmbedding()
	list := embed.ModelList()
	assert.Greater(t, len(list), 0)
}

func TestEmbeddingUnexistedModel(t *testing.T) {
	embed := NewEmbedding(WithModel("unexisted_model"))
	_, err := embed.Do(context.Background(), &EmbeddingRequest{
		Input: []string{"hello3"},
	})
	assert.Error(t, err)
	var target *ModelNotSupportedError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Model, "unexisted_model")
}

func TestEmbeddingDynamicEndpoint(t *testing.T) {
	defer resetTestEnv()
	embed := NewEmbedding(WithModel("embed-test"))
	resp, err := embed.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "embedding_list")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "embed_test")

	ebSpeed := NewEmbedding(WithModel("Embedding-V1"))
	resp, err = ebSpeed.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "embedding_list")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "embedding-v1")
}

func TestEmbeddingDynamicEndpointWhenAccessKeyUnavailable(t *testing.T) {
	defer resetTestEnv()
	GetConfig().AK = "test_ak"
	GetConfig().SK = "test_sk"
	GetConfig().AccessKey = ""
	GetConfig().SecretKey = ""
	embedding := NewEmbedding(WithModel("embed-test"))
	_, err := embedding.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.Error(t, err)
	var target *ModelNotSupportedError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Model, "embed-test")

	ebSpeed := NewEmbedding(WithModel("Embedding-V1"))
	resp, err := ebSpeed.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "embedding_list")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "embedding-v1")
}

func TestEmbeddingDynamicEndpointWhenNewModel(t *testing.T) {
	resetTestEnv()
	defer resetTestEnv()
	embed := NewEmbedding(WithModel("embed-test"))
	resp, err := embed.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "embedding_list")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "embed_test")

	// 缺少模型，应当尝试刷新
	delete(getModelEndpointRetriever().modelList["embeddings"], "embed-test")
	getModelEndpointRetriever().lastUpdate = time.Now().Add(-1 * time.Hour)

	resp, err = embed.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "embedding_list")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "embed_test")
}

func TestEmbeddingDynamicEndpointWhenEndpointError(t *testing.T) {
	resetTestEnv()
	defer resetTestEnv()
	comp := NewEmbedding(WithModel("embed-test"))
	resp, err := comp.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "embedding_list")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "embed_test")

	getModelEndpointRetriever().modelList["embeddings"]["embed-test"] = "/embeddings/error"
	getModelEndpointRetriever().lastUpdate = time.Now().Add(-1 * time.Hour)

	resp, err = comp.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "embedding_list")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "embed_test")

	comp = NewEmbedding(WithEndpoint("error"))
	_, err = comp.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.Error(t, err)
	apiErr := err.(*APIError)
	assert.Equal(t, apiErr.Code, UnsupportedMethodErrCode)

	getModelEndpointRetriever().modelList["embeddings"]["ERROR_MODEL"] = "/embeddings/error"
	comp = NewEmbedding(WithModel("ERROR_MODEL"))
	_, err = comp.Do(
		context.Background(),
		&EmbeddingRequest{
			Input: []string{"hello3"},
		},
	)
	assert.Error(t, err)
	apiErr = err.(*APIError)
	assert.Equal(t, apiErr.Code, UnsupportedMethodErrCode)
}
