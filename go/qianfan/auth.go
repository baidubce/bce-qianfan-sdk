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
	lock     sync.RWMutex
	*Requestor
}

var authManager = AuthManager{
	tokenMap:  make(map[credential]*accessToken),
	lock:      sync.RWMutex{},
	Requestor: newRequestor(makeOptions()),
}

func (m *AuthManager) GetAccessToken(ak, sk string) (string, error) {
	token, ok := func() (*accessToken, bool) {
		m.lock.RLock()
		defer m.lock.RUnlock()
		token, ok := m.tokenMap[credential{ak, sk}]
		return token, ok
	}()
	if ok {
		return token.token, nil
	}
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
		return "", fmt.Errorf("refresh access token failed: %s", resp.ErrorDescription)
	}
	m.tokenMap[credential{ak, sk}] = &accessToken{
		token:         resp.AccessToken,
		lastUpateTime: time.Now(),
	}
	return resp.AccessToken, nil
}
