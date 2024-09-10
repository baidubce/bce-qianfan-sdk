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

import "context"

// 用于 Text2Image 相关操作的结构体
type Text2Image struct {
	BaseModel
}

// Text2Image 请求
type Text2ImageRequest struct {
	BaseRequestBody `mapstructure:"-"`
	Prompt          string  `mapstructure:"prompt"`                    // 输入的提示词
	NegativePrompt  string  `mapstructure:"negative_prompt,omitempty"` // 反向提示词
	Size            string  `mapstructure:"size,omitempty"`            // 图片尺寸
	N               int     `mapstructure:"n,omitempty"`               // 生成图片的个数
	Steps           int     `mapstructure:"steps,omitempty"`           // 迭代论述
	SamplerIndex    string  `mapstructure:"sampler_index,omitempty"`   // 采样方式
	Seed            int     `mapstructure:"seed,omitempty"`            // 随机种子
	CfgScale        float64 `mapstructure:"cfg_scale,omitempty"`       // 提示词相关性
	Style           string  `mapstructure:"style,omitempty"`           // 风格
	UserID          string  `mapstructure:"user_id,omitempty"`         // 用户ID
}

// 具体的 Text2Image 信息
type Text2ImageData struct {
	Object      string `json:"object"`    // 固定值"image"
	Base64Image string `json:"b64_image"` // 图片base64编码内容
	Index       int    `json:"index"`     // 序号
}

// 返回的 Text2Image 数据
type Text2ImageResponse struct {
	Id            string           `json:"id"`      // 请求的id
	Object        string           `json:"object"`  // 回包类型，固定值“image”
	Created       int              `json:"created"` // 创建时间
	Usage         ModelUsage       `json:"usage"`   // 生成图片结果
	Data          []Text2ImageData `json:"data"`    // Text2Image 数据
	ModelAPIError                  // API 错误信息
	baseResponse                   // 基础的响应字段
}

// 内置 Text2Image 模型的 endpoint
var Text2ImageEndpoint = map[string]string{
	"Stable-Diffusion-XL": "/text2image/sd_xl",
}

// 创建 Text2Image 实例
func NewText2Image(optionList ...Option) *Text2Image {
	options := makeOptions(optionList...)
	return newText2Image(options)
}

// 内部根据 options 创建 Text2Image 实例
func newText2Image(options *Options) *Text2Image {
	text2img := &Text2Image{
		BaseModel{
			Model:     DefaultText2ImageModel,
			Endpoint:  "",
			Requestor: newRequestor(options),
		},
	}
	if options.Model != nil {
		text2img.Model = *options.Model
	}
	if options.Endpoint != nil {
		text2img.Endpoint = *options.Endpoint
	}
	return text2img
}

// endpoint 转成完整 url
func (c *Text2Image) realEndpoint(ctx context.Context) (string, error) {
	url := modelAPIPrefix
	if c.Endpoint == "" {
		endpoint := getModelEndpointRetriever().GetEndpoint(ctx, "text2image", c.Model)
		if endpoint == "" {
			endpoint = getModelEndpointRetriever().GetEndpointWithRefresh(ctx, "text2image", c.Model)
			if endpoint == "" {
				return "", &ModelNotSupportedError{Model: c.Model}
			}
		}
		url += endpoint
	} else {
		url += "/text2image/" + c.Endpoint
	}
	logger.Debugf("requesting endpoint: %s", url)
	return url, nil
}

// 发送 Text2Image 请求
func (c *Text2Image) Do(ctx context.Context, request *Text2ImageRequest) (*Text2ImageResponse, error) {
	var resp *Text2ImageResponse
	var err error
	runErr := runWithContext(ctx, func() {
		resp, err = c.do(ctx, request)
	})
	if runErr != nil {
		return nil, runErr
	}
	return resp, err
}

func (c *Text2Image) do(ctx context.Context, request *Text2ImageRequest) (*Text2ImageResponse, error) {
	do := func() (*Text2ImageResponse, error) {
		url, err := c.realEndpoint(ctx)
		if err != nil {
			return nil, err
		}
		req, err := NewModelRequest("POST", url, request)
		if err != nil {
			return nil, err
		}
		resp := &Text2ImageResponse{}

		err = c.requestResource(ctx, req, resp)
		if err != nil {
			return nil, err
		}

		return resp, nil
	}
	resp, err := do()
	if err != nil {
		if c.Endpoint == "" && isUnsupportedModelError(err) {
			// 根据 model 获得的 endpoint 错误，刷新模型列表后重试
			refreshErr := getModelEndpointRetriever().Refresh(ctx)
			if refreshErr != nil {
				logger.Errorf("refresh endpoint failed: %s", refreshErr)
				return resp, err
			}
			return do()
		}
		return resp, err
	}
	return resp, err
}

// 获取 Text2Image 支持的模型列表
func (c *Text2Image) ModelList() []string {
	models := getModelEndpointRetriever().GetModelList(context.TODO(), "text2image")
	list := make([]string, len(models))
	i := 0
	for k := range models {
		list[i] = k
		i++
	}
	return list
}
