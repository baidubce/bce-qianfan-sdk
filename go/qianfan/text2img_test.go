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

func TestText2Image(t *testing.T) {
	embed := NewText2Image()
	resp, err := embed.Do(context.Background(), &Text2ImageRequest{
		Prompt: "test",
	})
	assert.NoError(t, err)
	assert.Equal(t, resp.RawResponse.StatusCode, 200)
	assert.Equal(t, len(resp.Data), 1)
	assert.Contains(t, resp.RawResponse.Request.URL.Path, Text2ImageEndpoint[DefaultText2ImageModel])
	req, err := getRequestBody[Text2ImageRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, req.Prompt, "test")

	embed = NewText2Image(WithModel("Stable-Diffusion-XL"))
	resp, err = embed.Do(context.Background(), &Text2ImageRequest{
		Prompt: "test2",
	})
	assert.NoError(t, err)
	assert.Equal(t, resp.RawResponse.StatusCode, 200)
	assert.Equal(t, len(resp.Data), 1)
	assert.Contains(t, resp.RawResponse.Request.URL.Path, Text2ImageEndpoint["Stable-Diffusion-XL"])
	req, err = getRequestBody[Text2ImageRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, req.Prompt, "test2")

	embed = NewText2Image(WithEndpoint("custom_endpoint"))
	resp, err = embed.Do(context.Background(), &Text2ImageRequest{
		Prompt: "test3",
	})
	assert.NoError(t, err)
	assert.Equal(t, resp.RawResponse.StatusCode, 200)
	assert.Equal(t, len(resp.Data), 1)
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "custom_endpoint")
	req, err = getRequestBody[Text2ImageRequest](resp.RawResponse)
	assert.NoError(t, err)
	assert.Equal(t, req.Prompt, "test3")
}

func TestText2ImageModelList(t *testing.T) {
	embed := NewText2Image()
	list := embed.ModelList()
	assert.Greater(t, len(list), 0)
}

func TestText2ImageUnexistedModel(t *testing.T) {
	embed := NewText2Image(WithModel("unexisted_model"))
	_, err := embed.Do(context.Background(), &Text2ImageRequest{
		Prompt: "test",
	})
	assert.Error(t, err)
	var target *ModelNotSupportedError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Model, "unexisted_model")
}

func TestText2ImageDynamicEndpoint(t *testing.T) {
	Text2ImageEndpoint = map[string]string{}
	resetTestEnv()
	defer resetTestEnv()
	embed := NewText2Image(WithModel("Stable-Diffusion-XL"))
	resp, err := embed.Do(
		context.Background(),
		&Text2ImageRequest{
			Prompt: "test",
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "image")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "sd_xl")

}

func TestText2ImageDynamicEndpointWhenAccessKeyUnavailable(t *testing.T) {
	Text2ImageEndpoint = map[string]string{}
	resetTestEnv()
	defer resetTestEnv()
	GetConfig().AK = "test_ak"
	GetConfig().SK = "test_sk"
	GetConfig().AccessKey = ""
	GetConfig().SecretKey = ""
	Text2Image := NewText2Image(WithModel("Stable-Diffusion-XL"))
	_, err := Text2Image.Do(
		context.Background(),
		&Text2ImageRequest{
			Prompt: "test",
		},
	)
	assert.Error(t, err)
	var target *ModelNotSupportedError
	assert.ErrorAs(t, err, &target)
	assert.Equal(t, target.Model, "Stable-Diffusion-XL")

}

func TestText2ImageDynamicEndpointWhenNewModel(t *testing.T) {
	resetTestEnv()
	defer resetTestEnv()
	embed := NewText2Image(WithModel("Stable-Diffusion-XL"))
	resp, err := embed.Do(
		context.Background(),
		&Text2ImageRequest{
			Prompt: "test",
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "image")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "sd_xl")

	// 缺少模型，应当尝试刷新
	delete(getModelEndpointRetriever().modelList["text2image"], "Stable-Diffusion-XL")
	getModelEndpointRetriever().lastUpdate = time.Now().Add(-1 * time.Hour)

	resp, err = embed.Do(
		context.Background(),
		&Text2ImageRequest{
			Prompt: "test",
		},
	)
	assert.NoError(t, err)
	assert.Equal(t, resp.Object, "image")
	assert.Contains(t, resp.RawResponse.Request.URL.Path, "sd_xl")
}
