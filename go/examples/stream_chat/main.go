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

package main

import (
	"context"
	"fmt"

	"github.com/baidubce/bce-qianfan-sdk/go/qianfan"
)

// 实现了简易的能够在命令行与 LLM 聊天的程序，并使用流式输出，加快响应速度
func main() {
	// 使用前请先设置 AccessKey 和 SecretKey，通过环境变量设置可省略如下两行
	// qianfan.GetConfig().AccessKey = "your_access_key"
	// qianfan.GetConfig().SecretKey = "your_secret_key"

	chat := qianfan.NewChatCompletion(
		qianfan.WithModel("ERNIE-Bot-4"),
	)
	chatHistory := []qianfan.ChatCompletionMessage{}

	for {
		var userMsg string
		fmt.Println("User Input:")
		fmt.Scan(&userMsg)
		fmt.Println()

		chatHistory = append(chatHistory, qianfan.ChatCompletionUserMessage(userMsg))

		stream, err := chat.Stream(context.TODO(), &qianfan.ChatCompletionRequest{
			Messages: chatHistory,
		})

		if err != nil {
			panic(err)
		}

		fmt.Println("Assistant Output:")
		var outputMsg string
		for {
			r, err := stream.Recv()
			if err != nil {
				panic(err)
			}
			if r.IsEnd {
				break
			}
			fmt.Print(r.Result)
			outputMsg = outputMsg + r.Result
		}
		chatHistory = append(chatHistory, qianfan.ChatCompletionAssistantMessage(outputMsg))
		fmt.Print("\n\n")
	}
}
