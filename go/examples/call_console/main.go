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
// 展示了如何获取所有可用的模型
package main

import (
	"context"
	"fmt"

	"github.com/baidubce/bce-qianfan-sdk/go/qianfan"
)

func main() {
	// 使用前请先设置 AccessKey 和 SecretKey，通过环境变量设置可省略如下两行
	// qianfan.GetConfig().AccessKey = "your_access_key"
	// qianfan.GetConfig().SecretKey = "your_secret_key"
	ca := qianfan.NewConsoleAction()
	// v2 console api
	res, err := ca.Call(context.TODO(), "/v2/memory", "CreateSystemMemory", map[string]interface{}{
		"appId":       "2xxxxxx2",
		"description": "test da系统人设描述",
	})
	if err != nil {
		panic(err)
	}
	fmt.Println(string(res.Body))

	// v1 console api
	res, err = ca.Call(context.TODO(), "/wenxinworkshop/service/list", "", map[string]interface{}{})
	if err != nil {
		panic(err)
	}
	fmt.Println(string(res.Body))
}
