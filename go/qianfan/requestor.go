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
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/baidubce/bce-sdk-go/auth"
	bceHTTP "github.com/baidubce/bce-sdk-go/http"
	"github.com/baidubce/bce-sdk-go/util"
)

// 所有请求类型需实现的接口
//
// 定义了提供额外参数的接口
type RequestBody interface {
	SetExtra(m map[string]interface{})
	GetExtra() map[string]interface{}
}

// 请求体基类
//
// 实现了允许用户传递额外参数的方法
type BaseRequestBody struct {
	Extra map[string]interface{} `mapstructure:"-"`
}

// 设置额外参数
func (r *BaseRequestBody) SetExtra(m map[string]interface{}) {
	r.Extra = m
}

// 获取额外参数
func (r *BaseRequestBody) GetExtra() map[string]interface{} {
	return r.Extra
}

// 将请求设置为流式
func (r *BaseRequestBody) SetStream() {
	if r.Extra == nil {
		r.Extra = map[string]interface{}{}
	}
	r.Extra["stream"] = true
}

// 将请求体转换成 map，并将额外参数合并到 map 中
func convertToMap(body RequestBody) (map[string]interface{}, error) {
	m, err := dumpToMap(body)
	if err != nil {
		return nil, err
	}
	extra := body.GetExtra()
	for k, v := range extra {
		m[k] = v
	}
	return m, nil
}

// 请求类型，用于区分是模型的请求还是管控类请求
// 在 QfRequest.Type 处被使用
const (
	authRequest             = "auth" // AccessToken 鉴权请求
	modelRequest            = "model"
	consoleRequest          = "console"
	bearerTokenRequest      = "bearer"
	fetchBearerTokenRequest = "fetchBearerToken"
)

// SDK 内部表示请求的类
type QfRequest struct {
	Type    string                 // 请求类型，用于区分是模型的请求 `modelRequest` 还是管控类请求 `consoleRequest`
	Method  string                 // HTTP 方法
	URL     string                 // 请求的完整地址
	Headers map[string]string      // HTTP 请求头
	Params  map[string]string      // HTTP 请求参数
	Body    map[string]interface{} // HTTP 请求体
}

// 创建一个用于模型类请求的 Request
func NewModelRequest(method string, url string, body RequestBody) (*QfRequest, error) {
	return newRequest(modelRequest, method, url, body)
}

// 创建一个用于鉴权类请求的 Request
func newAuthRequest(method string, url string, body RequestBody) (*QfRequest, error) {
	return newRequest(authRequest, method, url, body)
}

// 创建一个用于管控类请求的 Request
func NewConsoleRequest(method string, url string, body RequestBody) (*QfRequest, error) {
	return newRequest(consoleRequest, method, url, body)
}

// 创建一个使用Bearer Token鉴权的 Request
func NewBearerTokenRequest(method string, url string, body RequestBody) (*QfRequest, error) {
	return newRequest(bearerTokenRequest, method, url, body)
}

// 创建一个使用Bearer Token鉴权的 Request
func NewIAMBearerTokenRequest(method string, url string, body RequestBody) (*QfRequest, error) {
	return newRequest(fetchBearerTokenRequest, method, url, body)
}

// 创建一个 Request，body 可以是任意实现了 RequestBody 接口的类型
func newRequest(requestType string, method string, url string, body RequestBody) (*QfRequest, error) {
	var b map[string]interface{} = nil
	if body != nil {
		bodyMap, err := convertToMap(body)
		if err != nil {
			return nil, err
		}
		b = bodyMap
	}
	return newRequestFromMap(requestType, method, url, b)
}

// 创建一个 Request，body 是一个 map
func newRequestFromMap(requestType string, method string, urlStr string, body map[string]interface{}) (*QfRequest, error) {
	u, err := url.Parse(urlStr)
	if err != nil {
		return nil, err
	}

	// 提取params
	params := u.Query()
	paramsMap := make(map[string]string)
	for key, values := range params {
		if len(values) > 0 {
			paramsMap[key] = values[0] // 只取第一个值
		}
	}

	return &QfRequest{
		Type:    requestType,
		Method:  method,
		URL:     u.Path,
		Body:    body,
		Params:  paramsMap,
		Headers: map[string]string{},
	}, nil
}

// 所有回复类型的基类
type baseResponse struct {
	Body        []byte
	RawResponse *http.Response `json:"-"`
}

// 所有回复类型需实现的接口
type QfResponse interface {
	SetResponse(Body []byte, RawResponse *http.Response)
	GetResponse() *http.Response
	GetErrorCode() string
}

// 设置回复中通用参数的字段
func (r *baseResponse) SetResponse(Body []byte, RawResponse *http.Response) {
	r.Body = Body
	r.RawResponse = RawResponse
}

func (r *baseResponse) GetResponse() *http.Response {
	return r.RawResponse
}

// 请求器，负责 SDK 中所有请求的发送，是所有对外暴露对象的基类
type Requestor struct {
	client  *http.Client
	Options *Options
}

// 创建一个 Requestor
func newRequestor(options *Options) *Requestor {
	r := &Requestor{
		client:  &http.Client{},
		Options: options,
	}
	if r.Options.LLMRetryTimeout != 0 {
		r.client.Timeout = time.Duration(r.Options.LLMRetryTimeout) * time.Second
	}
	return r
}

func (r *Requestor) addAuthInfo(ctx context.Context, request *QfRequest) error {
	if request.Type == authRequest {
		return nil
	}
	if request.Type == bearerTokenRequest {
		token, err := GetBearerToken()
		if err != nil {
			return err
		}
		request.Headers["Authorization"] = fmt.Sprintf("Bearer %s", token)
		return nil
	}
	if GetConfig().AK != "" && GetConfig().SK != "" {
		return r.addAccessToken(ctx, request)
	} else if GetConfig().AccessKey != "" && GetConfig().SecretKey != "" {
		return r.sign(request)
	} else if GetConfig().AccessToken != "" {
		request.Params["access_token"] = GetConfig().AccessToken
		return nil
	}
	logger.Error("no enough credential found. Please check whether (ak, sk) or (access_key, secret_key) or (access_token) is set in config")
	return &CredentialNotFoundError{}
}

// 增加 accesstoken 鉴权信息
func (r *Requestor) addAccessToken(ctx context.Context, request *QfRequest) error {
	token, err := GetAuthManager().GetAccessToken(ctx, GetConfig().AK, GetConfig().SK)
	if err != nil {
		return err
	}
	request.Params["access_token"] = token
	return nil
}

// IAM 签名
func (r *Requestor) sign(request *QfRequest) error {
	bceRequest := &bceHTTP.Request{}
	bceRequest.SetMethod(request.Method)
	bceRequest.SetHeaders(request.Headers)
	bceRequest.SetParams(request.Params)
	u, err := url.Parse(request.URL)
	if err != nil {
		return err
	}
	bceRequest.SetProtocol(u.Scheme)

	bceRequest.SetHost(u.Hostname())
	port := u.Port()
	if port == "" {
		if u.Scheme == "http" {
			port = "80"
		} else if u.Scheme == "https" {
			port = "443"
		} else {
			logger.Errorf("Got unexpected protocol `%s` in requested API url `%s`.", u.Scheme, request.URL)
			return &InvalidParamError{
				Msg: fmt.Sprintf("unrecognized protocol `%s` is set in API base url."+
					"Only http and https are supported.", u.Scheme),
			}
		}
	}
	porti, err := strconv.Atoi(port)
	if err != nil {
		return err
	}
	bceRequest.SetPort(porti)
	bceRequest.SetUri(u.RequestURI())

	credentials := &auth.BceCredentials{
		AccessKeyId:     GetConfig().AccessKey,
		SecretAccessKey: GetConfig().SecretKey,
	}
	now := util.NowUTCSeconds()
	bceRequest.SetHeader("Host", u.Hostname())
	bceRequest.SetHeader("x-bce-date", util.FormatISO8601Date(now))
	headersToSign := make(map[string]struct{})
	for k := range bceRequest.Headers() {
		headersToSign[strings.ToLower(k)] = struct{}{}
	}
	signer := auth.BceV1Signer{}
	signOptions := &auth.SignOptions{
		HeadersToSign: headersToSign,
		Timestamp:     now,
		ExpireSeconds: GetConfig().IAMSignExpirationSeconds,
	}
	signer.Sign(bceRequest, credentials, signOptions)

	request.Headers = bceRequest.Headers()
	return nil
}

// 对请求进行统一处理，并转换成 http.Request
func (r *Requestor) prepareRequest(ctx context.Context, request QfRequest) (*http.Request, error) {
	// 设置溯源标识
	if request.Type == modelRequest {
		request.URL = GetConfig().BaseURL + request.URL
		if _, ok := request.Body["extra_parameters"]; !ok {
			request.Body["extra_parameters"] = map[string]interface{}{}
		}
		request.Body["extra_parameters"].(map[string]interface{})["request_source"] = versionIndicator
	} else if request.Type == consoleRequest {
		request.URL = GetConfig().ConsoleBaseURL + request.URL
		request.Headers["request-source"] = versionIndicator
	} else if request.Type == authRequest {
		request.URL = GetConfig().BaseURL + request.URL
	} else if request.Type == bearerTokenRequest {
		request.URL = GetConfig().ConsoleBaseURL + request.URL
		request.Headers["request-source"] = versionIndicator
	} else if request.Type == fetchBearerTokenRequest {
		request.URL = GetConfig().IAMBaseURL + request.URL
	} else {
		return nil, &InternalError{"unexpected request type: " + request.Type}
	}
	bodyBytes, err := json.Marshal(request.Body)
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequest(request.Method, request.URL, bytes.NewBuffer(bodyBytes))
	if err != nil {
		return nil, err
	}
	request.Headers["Content-Type"] = "application/json"
	// 增加鉴权信息
	err = r.addAuthInfo(ctx, &request)
	if err != nil {
		return nil, err
	}
	for k, v := range request.Headers {
		req.Header.Set(k, v)
	}

	q := req.URL.Query()
	for k, v := range request.Params {
		q.Add(k, v)
	}
	req.URL.RawQuery = q.Encode()

	return req, nil
}

// 进行请求，返回原始的 baseResponse，并将结果解析至 resp
func (r *Requestor) request(ctx context.Context, request *QfRequest, response QfResponse) error {
	req, err := r.prepareRequest(ctx, *request)
	if err != nil {
		return err
	}
	err = r.sendRequestAndParse(ctx, req, response)
	if err != nil {
		return err
	}
	return nil
}

func (r *Requestor) sendRequestAndParse(ctx context.Context, request *http.Request, response QfResponse) error {
	resp, err := r.client.Do(request.WithContext(ctx))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	response.SetResponse(body, resp)
	err = json.Unmarshal(body, response)
	if err != nil {
		return err
	}

	return nil
}

// 流的内部实现，用于接收流中的响应
type streamInternal struct {
	*Requestor                                  // 请求器
	requestFunc  func() (*http.Response, error) // 请求流中的响应的函数
	httpResponse *http.Response                 // 原始的 http.Response
	scanner      *bufio.Scanner                 // 读取流的 scanner
	IsEnd        bool                           // 流是否已经结束
	context      context.Context                // 流所使用的 context
}

// 创建一个流
func newStreamInternal(ctx context.Context, requestor *Requestor, requestFunc func() (*http.Response, error)) (*streamInternal, error) {
	si := &streamInternal{
		Requestor:    requestor,
		requestFunc:  requestFunc,
		httpResponse: nil,
		scanner:      nil,
		IsEnd:        false,
		context:      ctx,
	}
	// 初始化请求
	err := si.reset()
	if err != nil {
		return nil, err
	}
	return si, nil
}

func (si *streamInternal) reset() error {
	response, err := si.requestFunc()
	si.IsEnd = false
	if err != nil {
		si.IsEnd = true
		return err
	}
	si.httpResponse = response

	return nil
}

func (si *streamInternal) RawResponse() *http.Response {
	return si.httpResponse
}

// 关闭流
func (si *streamInternal) Close() {
	_ = si.httpResponse.Body.Close()
}

// 接受流中的响应，并将结果解析至 resp
func (si *streamInternal) Recv(resp QfResponse) error {
	var err error
	runErr := runWithContext(si.context, func() {
		err = si.recv(resp)
	})
	if runErr != nil {
		logger.Warnf("Stream operation cancelled due to context, error: %s", runErr)
		return runErr
	}
	return err
}

func (si *streamInternal) recv(resp QfResponse) error {
	var eventData []byte
	if si.scanner == nil {
		si.scanner = bufio.NewScanner(si.httpResponse.Body)
	}
	for len(eventData) == 0 {
		for {
			if !si.scanner.Scan() {
				si.IsEnd = true
				si.Close()
				if si.scanner.Err() != nil || len(eventData) == 0 {
					return si.scanner.Err()
				}
				break
			}

			line := si.scanner.Bytes()
			if len(line) == 0 {
				break
			}
			var (
				// field []byte = line
				value []byte
			)
			if i := bytes.Index(line, []byte("event")); i != -1 {
				continue
			}
			if i := bytes.IndexRune(line, ':'); si.httpResponse.StatusCode == http.StatusOK && i != -1 {
				// field = line[:i]
				value = line[i+1:]
				if len(value) != 0 && value[0] == ' ' {
					value = value[1:]
				}
			} else {
				value = line[:]
			}
			eventData = append(eventData, value...)
		}
	}
	response := baseResponse{
		Body:        eventData,
		RawResponse: si.httpResponse,
	}

	if string(eventData) == "[DONE]" {
		si.IsEnd = true
		si.Close()
		return nil
	}

	resp.SetResponse(response.Body, response.RawResponse)
	err := json.Unmarshal(response.Body, resp)
	if err != nil {
		si.IsEnd = true
		return err
	}
	return nil
}

// 发送请求，返回流对象
func (r *Requestor) requestStream(ctx context.Context, request *QfRequest) (*streamInternal, error) {
	sendRequest := func() (*http.Response, error) {
		req, err := r.prepareRequest(ctx, *request)
		if err != nil {
			return nil, err
		}
		resp, err := r.client.Do(req.WithContext(ctx))
		if err != nil {
			return nil, err
		}
		return resp, nil
	}

	return newStreamInternal(ctx, r, sendRequest)
}
