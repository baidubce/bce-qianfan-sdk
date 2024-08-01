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
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func fakeAccessToken(ak, sk string) string {
	return fmt.Sprintf("%s.%s", ak, sk)
}

func setAccessTokenExpired(ak, sk string) {
	GetAuthManager().tokenMap[credential{ak, sk}] = &accessToken{
		token:         "expired_token",
		lastUpateTime: time.Now().Add(-100 * time.Hour), // 100s 过期
	}
}

func TestAuth(t *testing.T) {
	resetAuthManager()
	ctx := context.TODO()
	ak, sk := "ak_33", "sk_4235"
	// 第一次获取前，缓存里应当没有
	_, ok := GetAuthManager().tokenMap[credential{ak, sk}]
	assert.False(t, ok)

	accessTok, err := GetAuthManager().GetAccessToken(ctx, ak, sk)
	assert.NoError(t, err)
	assert.Equal(t, accessTok, fakeAccessToken(ak, sk))
	updateTime := GetAuthManager().tokenMap[credential{ak, sk}].lastUpateTime
	// 再测试一次，应当从缓存里获取，更新时间不变
	accessTok, err = GetAuthManager().GetAccessToken(ctx, ak, sk)
	assert.NoError(t, err)
	assert.Equal(t, accessTok, fakeAccessToken(ak, sk))
	assert.Equal(
		t,
		updateTime,
		GetAuthManager().tokenMap[credential{ak, sk}].lastUpateTime,
	)
	// 模拟过期
	ak, sk = "ak_95411", "sk_87135"
	setAccessTokenExpired(ak, sk)
	// 设置一个附近的更新时间，用来测试是否会忽略刚更新过的 token
	GetAuthManager().tokenMap[credential{ak, sk}].lastUpateTime = time.Now()

	accessTok, err = GetAuthManager().GetAccessToken(ctx, ak, sk)
	assert.NoError(t, err)
	assert.Equal(t, accessTok, "expired_token") // 直接获取还是从缓存获取

	accessTok, err = GetAuthManager().GetAccessTokenWithRefresh(ctx, ak, sk)
	assert.NoError(t, err)
	assert.Equal(t, accessTok, "expired_token") // 刷新后，由于 lastUpdateTime 太接近，依旧使用缓存
	setAccessTokenExpired(ak, sk)

	accessTok, err = GetAuthManager().GetAccessTokenWithRefresh(ctx, ak, sk)
	assert.NoError(t, err)
	assert.Equal(t, accessTok, fakeAccessToken(ak, sk)) // 应当刷新
	elaplsed := time.Since(GetAuthManager().tokenMap[credential{ak, sk}].lastUpateTime)
	assert.Less(t, elaplsed, 10*time.Second) // 刷新后，lastUpdateTime 应当更新
}

func TestAuthFailed(t *testing.T) {
	ak, sk := "bad_ak", "bad_sk"
	_, err := GetAuthManager().GetAccessToken(context.TODO(), ak, sk)
	assert.Error(t, err)
	var target *APIError
	assert.ErrorAs(t, err, &target)
	assert.Contains(t, err.Error(), target.Msg)
	assert.Equal(t, target.Msg, "Client authentication failed")
}

func TestAuthWhenUsing(t *testing.T) {
	defer resetTestEnv()
	resetAuthManager()
	GetConfig().AccessKey = "access_key_484913"
	GetConfig().SecretKey = "secret_key_48135"
	GetConfig().AK = ""
	GetConfig().SK = ""
	// 未设置 AKSK，所以用 IAM 鉴权
	chat := NewChatCompletion()
	resp, err := chat.Do(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{ChatCompletionUserMessage("你好")},
		},
	)
	assert.NoError(t, err)
	signedKey, ok := resp.RawResponse.Request.Header["Authorization"]
	assert.True(t, ok)
	assert.Contains(t, signedKey[0], GetConfig().AccessKey)
	assert.NotContains(t, resp.RawResponse.Request.URL.RawQuery, "access_token")
	// 设置了 AKSK，所以用 AKSK 鉴权
	GetConfig().AK = "ak_48915684"
	GetConfig().SK = "sk_78941813"
	resp, err = chat.Do(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{ChatCompletionUserMessage("你好")},
		},
	)
	assert.NoError(t, err)
	_, ok = resp.RawResponse.Request.Header["Authorization"]
	assert.False(t, ok)
	assert.Contains(t, resp.RawResponse.Request.URL.RawQuery, "access_token")
	assert.Equal(
		t,
		resp.RawResponse.Request.URL.Query().Get("access_token"),
		fakeAccessToken(GetConfig().AK, GetConfig().SK),
	)
	// 如果只设置了部分鉴权信息，则报错
	GetConfig().AK = ""
	GetConfig().AccessKey = ""
	GetConfig().AccessToken = ""
	_, err = chat.Do(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{ChatCompletionUserMessage("你好")},
		},
	)
	assert.Error(t, err)
	var target *CredentialNotFoundError
	assert.ErrorAs(t, err, &target)
}

func TestAccessTokenExpired(t *testing.T) {
	defer resetTestEnv()
	resetAuthManager()
	ctx := context.TODO()
	ak, sk := "ak_48915684", "sk_78941813"
	GetConfig().AK = ak
	GetConfig().SK = sk
	setAccessTokenExpired(ak, sk)
	token, err := GetAuthManager().GetAccessToken(ctx, ak, sk)
	assert.NoError(t, err)
	assert.Contains(t, token, "expired")
	prompt := "你好"
	chat := NewChatCompletion()
	resp, err := chat.Do(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{ChatCompletionUserMessage(prompt)},
		},
	)
	assert.NoError(t, err)
	assert.Contains(t, resp.RawResponse.Request.URL.Query().Get("access_token"), fakeAccessToken(ak, sk))
	assert.Contains(t, resp.Result, prompt)
	token, err = GetAuthManager().GetAccessToken(ctx, ak, sk)
	assert.NoError(t, err)
	assert.Equal(t, token, fakeAccessToken(ak, sk))

	// 测试流式请求的刷新 token
	setAccessTokenExpired(ak, sk)
	token, err = GetAuthManager().GetAccessToken(ctx, ak, sk)
	assert.NoError(t, err)
	assert.Contains(t, token, "expired")
	stream, err := chat.Stream(
		context.Background(),
		&ChatCompletionRequest{
			Messages: []ChatCompletionMessage{ChatCompletionUserMessage(prompt)},
		},
	)
	assert.NoError(t, err)

	for {
		r, err := stream.Recv()
		assert.NoError(t, err)
		token, err = GetAuthManager().GetAccessToken(ctx, ak, sk)
		assert.NoError(t, err)
		assert.Equal(t, token, fakeAccessToken(ak, sk))
		assert.Contains(t, r.RawResponse.Request.URL.Query().Get("access_token"), fakeAccessToken(ak, sk))
		if r.IsEnd {
			break
		}
	}

}
