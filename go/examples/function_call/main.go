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
// 展示如何调用模型的 function call 能力
package main

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/baidubce/bce-qianfan-sdk/go/qianfan"
)

func GetWeather(city string) map[string]string {
	return map[string]string{
		"weather":     "多云",
		"temperature": "25",
	}
}

var WeatherFunc = qianfan.Function{
	Name:        "GetWeather",
	Description: "获取某个城市的天气",
	Parameters: map[string]any{
		"type": "object",
		"properties": map[string]any{
			"city": map[string]any{
				"type":        "string",
				"description": "所要查询天气的城市名称",
			},
		},
		"required": []string{"city"},
	},
}

func main() {
	// 使用前请先设置 AccessKey 和 SecretKey，通过环境变量设置可省略如下两行
	// qianfan.GetConfig().AccessKey = "your_access_key"
	// qianfan.GetConfig().SecretKey = "your_secret_key"

	chat := qianfan.NewChatCompletion(
		qianfan.WithModel("ERNIE-3.5-8K"), // 利用 ERNIE-3.5-8K 模型的 function call 能力
	)
	messages := []qianfan.ChatCompletionMessage{
		qianfan.ChatCompletionUserMessage("请帮我查询一下上海今天的天气"),
	}
	functions := []qianfan.Function{
		WeatherFunc,
	}

	resp, err := chat.Do(
		context.TODO(),
		&qianfan.ChatCompletionRequest{
			Messages:  messages,
			Functions: functions,
		},
	)
	if err != nil {
		panic(err)
	}
	messages = append(messages, qianfan.ChatCompletionMessage{
		Role:         "assistant",
		FunctionCall: resp.FunctionCall,
	})

	// 获取模型返回的函数调用信息
	m := make(map[string]any)
	json.Unmarshal([]byte(resp.FunctionCall.Arguments), &m)

	// 根据参数调用函数
	city := m["city"].(string)
	weather := GetWeather(city)

	// 并将结果返回给模型
	funcResultStr, err := json.Marshal(weather)
	if err != nil {
		panic(err)
	}
	messages = append(messages, qianfan.ChatCompletionMessage{
		Role:    "function",
		Name:    "GetWeather",
		Content: string(funcResultStr),
	})

	funcResp, err := chat.Do(
		context.TODO(),
		&qianfan.ChatCompletionRequest{
			Messages:  messages,
			Functions: functions,
		},
	)
	if err != nil {
		panic(nil)
	}

	// 打印模型根据函数调用结果输出的回复
	fmt.Println(string(funcResp.Result))
}
