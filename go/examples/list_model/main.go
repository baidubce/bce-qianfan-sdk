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

import "github.com/baidubce/bce-qianfan-sdk/go/qianfan"

func main() {
	// 根据用途选择
	u := qianfan.NewChatCompletion()
	// u := qianfan.NewCompletion()
	// u := qianfan.NewEmbedding()

	for _, m := range u.ModelList() {
		println(m)
	}
}
