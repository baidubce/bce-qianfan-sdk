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

// 千帆 SDK 示例代码
// 实现了文生图功能
package main

import (
	"context"
	"encoding/base64"
	"fmt"
	"os"

	"github.com/baidubce/bce-qianfan-sdk/go/qianfan"
)

func main() {
	// 使用前请先设置 AccessKey 和 SecretKey，通过环境变量设置可省略如下两行
	// qianfan.GetConfig().AccessKey = "your_access_key"
	// qianfan.GetConfig().SecretKey = "your_secret_key"

	outputFile := "output.jpg"
	text2img := qianfan.NewText2Image(
		qianfan.WithModel("Stable-Diffusion-XL"),
	)

	var prompt string
	fmt.Println("Please input prompt:")
	fmt.Scan(&prompt)
	fmt.Println()

	resp, err := text2img.Do(context.TODO(), &qianfan.Text2ImageRequest{
		Prompt: prompt,
	})
	if err != nil {
		panic(err)
	}

	img := resp.Data[0].Base64Image
	imgData, err := base64.StdEncoding.DecodeString(img)
	if err != nil {
		panic(err)
	}

	f, err := os.Create(outputFile)
	if err != nil {
		panic(err)
	}
	defer func() {
		if err := f.Close(); err != nil {
			panic(err)
		}
	}()

	_, err = f.Write(imgData)
	if err != nil {
		panic(err)
	}
	fmt.Printf("Image saved to %s\n", outputFile)
}
