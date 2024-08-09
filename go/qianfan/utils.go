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

	"github.com/mitchellh/mapstructure"
)

// 转换任意对象成 map
func dumpToMap(input interface{}) (map[string]interface{}, error) {
	target := map[string]interface{}{}
	err := mapstructure.Decode(input, &target)
	if err != nil {
		return nil, err
	}
	return target, nil
}

func runWithContext(ctx context.Context, fn func()) error {
	c := make(chan struct{}, 1)
	go func() {
		fn()
		c <- struct{}{}
	}()

	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-c:
		return nil
	}
}

func contains(s []int, e int) bool {
	for _, a := range s {
		if a == e {
			return true
		}
	}
	return false
}
