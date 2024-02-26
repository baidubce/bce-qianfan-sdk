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
	chat := qianfan.NewChatCompletion(
		qianfan.WithModel("ERNIE-Bot"),
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

	m := make(map[string]any)
	json.Unmarshal([]byte(resp.FunctionCall.Arguments), &m)

	city := m["city"].(string)
	weather := GetWeather(city)
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

	fmt.Println(string(funcResp.Result))
}
