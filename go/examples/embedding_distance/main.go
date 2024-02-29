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
// 展示了如何使用千帆提供的 Embedding 模型，并计算两个文本的余弦距离
package main

import (
	"context"
	"fmt"
	"math"

	"github.com/baidubce/bce-qianfan-sdk/go/qianfan"
)

func cosDistance(embed1, embed2 []float64) (float64, error) {
	length := len(embed1)
	if length != len(embed2) {
		return -1, fmt.Errorf("length of embed1 and embed2 must be the same")
	}
	s1 := 0.0
	s2 := 0.0
	sum := 0.0
	for i := 0; i < length; i++ {
		s1 += math.Pow(embed1[i], 2)
		s2 += math.Pow(embed2[i], 2)
		sum += embed1[i] * embed2[i]
	}
	return sum / (math.Sqrt(s1) * math.Sqrt(s2)), nil

}

func main() {
	// 使用前请先设置 AccessKey 和 SecretKey，通过环境变量设置可省略如下两行
	// qianfan.GetConfig().AccessKey = "your_access_key"
	// qianfan.GetConfig().SecretKey = "your_secret_key"

	sentence1 := "你好"
	sentence2 := "hello"

	embed := qianfan.NewEmbedding()
	resp, err := embed.Do(context.TODO(), &qianfan.EmbeddingRequest{
		Input: []string{sentence1, sentence2},
	})
	if err != nil {
		panic(err)
	}
	embed1 := resp.Data[0].Embedding
	embed2 := resp.Data[1].Embedding

	distance, err := cosDistance(embed1, embed2)
	if err != nil {
		panic(err)
	}
	fmt.Println(distance)
}
