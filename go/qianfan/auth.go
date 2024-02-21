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
	"fmt"
	"sync"
	"time"

	"github.com/mitchellh/mapstructure"
)

type AccessTokenRequest struct {
	GrantType    string `mapstructure:"grant_type"`
	ClientId     string `mapstructure:"client_id"`
	ClientSecret string `mapstructure:"client_secret"`
}

func newAccessTokenRequest(ak, sk string) *AccessTokenRequest {
	return &AccessTokenRequest{
		GrantType:    "client_credentials",
		ClientId:     ak,
		ClientSecret: sk,
	}
}

type AccessTokenResponse struct {
	AccessToken      string `json:"access_token"`
	ExpiresIn        int    `json:"expires_in"`
	Error            string `json:"error"`
	ErrorDescription string `json:"error_description"`
	SessionKey       string `json:"session_key"`
	RefreshToken     string `json:"refresh_token"`
	Scope            string `json:"scope"`
	SessionSecret    string `json:"session_secret"`
	baseResponse
}

func (r *AccessTokenResponse) GetErrorCode() string {
	return r.Error
}

type credential struct {
	AK string
	SK string
}

type accessToken struct {
	token         string
	lastUpateTime time.Time
}

type AuthManager struct {
	tokenMap map[credential]*accessToken
	lock     sync.Mutex
	*Requestor
}

func maskAk(ak string) string {
	unmaskLen := 6
	if len(ak) < unmaskLen {
		return ak
	}
	return fmt.Sprintf("%s******", ak[:unmaskLen])
}

var _authManager *AuthManager

func GetAuthManager() *AuthManager {
	if _authManager == nil {
		_authManager = &AuthManager{
			tokenMap:  make(map[credential]*accessToken),
			lock:      sync.Mutex{},
			Requestor: newRequestor(makeOptions()),
		}
	}
	return _authManager
}

func (m *AuthManager) GetAccessToken(ak, sk string) (string, error) {
	token, ok := func() (*accessToken, bool) {
		m.lock.Lock()
		defer m.lock.Unlock()
		token, ok := m.tokenMap[credential{ak, sk}]
		return token, ok
	}()
	if ok {
		return token.token, nil
	}
	logger.Infof("Access token of ak `%s` not found, tring to refresh it...", maskAk(ak))
	return m.GetAccessTokenWithRefresh(ak, sk)
}

func (m *AuthManager) GetAccessTokenWithRefresh(ak, sk string) (string, error) {
	m.lock.Lock()
	defer m.lock.Unlock()

	token, ok := m.tokenMap[credential{ak, sk}]
	if ok {
		lastUpdate := token.lastUpateTime
		current := time.Now()
		// 最近更新时间小于最小刷新间隔，则直接返回
		// 避免多个请求同时刷新，导致token被刷新多次
		if current.Sub(lastUpdate) < time.Duration(GetConfig().AccessTokenRefreshMinInterval)*time.Second {
			logger.Debugf("Access token of ak `%s` was freshed %s ago, skip refreshing", maskAk(ak), current.Sub(lastUpdate))
			return token.token, nil
		}
	}

	resp := AccessTokenResponse{}
	req, err := newAuthRequest("POST", authAPIPrefix, nil)
	if err != nil {
		return "", err
	}
	params := newAccessTokenRequest(ak, sk)
	paramsMap := make(map[string]string)
	err = mapstructure.Decode(params, &paramsMap)
	if err != nil {
		return "", err
	}
	req.Params = paramsMap
	err = m.Requestor.request(req, &resp)
	if err != nil {
		return "", err
	}
	if resp.Error != "" {
		logger.Errorf("refresh access token of ak `%s` failed with error: %s", maskAk(ak), resp.ErrorDescription)
		return "", &APIError{Msg: resp.ErrorDescription}
	}
	logger.Infof("Access token of ak `%s` was refreshed", maskAk(ak))
	m.tokenMap[credential{ak, sk}] = &accessToken{
		token:         resp.AccessToken,
		lastUpateTime: time.Now(),
	}
	return resp.AccessToken, nil
}
