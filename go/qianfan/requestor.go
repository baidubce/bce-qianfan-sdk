package qianfan

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"github.com/baidubce/bce-sdk-go/auth"
	bceHTTP "github.com/baidubce/bce-sdk-go/http"
	"github.com/baidubce/bce-sdk-go/util"
)

// 所有请求的基类
type RequestBody[T any] interface {
	WithExtra(m map[string]interface{}) T
	GetExtra() map[string]interface{}
}

type BaseRequestBody struct {
	Extra map[string]interface{} `mapstructure:"-"`
}

func (r BaseRequestBody) WithExtra(m map[string]interface{}) BaseRequestBody {
	r.Extra = m
	return r
}

func (r BaseRequestBody) GetExtra() map[string]interface{} {
	return r.Extra
}

func (r *BaseRequestBody) SetStream() {
	if r.Extra == nil {
		r.Extra = map[string]interface{}{}
	}
	r.Extra["stream"] = true
}

func convertToMap[T RequestBody[T]](body T) (map[string]interface{}, error) {
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
// 用在 QfRequest.Type
const (
	ModelRequest   = "model"
	ConsoleRequest = "console"
)

type QfRequest struct {
	Type    string
	Method  string
	URL     string
	Headers map[string]string
	Params  map[string]string
	Body    map[string]interface{}
}

func newModelRequest[T RequestBody[T]](method string, url string, body T) (*QfRequest, error) {
	return newRequest(ModelRequest, method, url, body)
}

func newConsoleRequest[T RequestBody[T]](method string, url string, body T) (*QfRequest, error) {
	return newRequest(ConsoleRequest, method, url, body)
}

func newRequest[T RequestBody[T]](requestType string, method string, url string, body T) (*QfRequest, error) {
	b, err := convertToMap(body)
	if err != nil {
		return nil, err
	}
	return newRequestFromMap(requestType, method, url, b)
}

func newRequestFromMap(requestType string, method string, url string, body map[string]interface{}) (*QfRequest, error) {
	return &QfRequest{
		Type:    requestType,
		Method:  method,
		URL:     url,
		Body:    body,
		Params:  map[string]string{},
		Headers: map[string]string{},
	}, nil
}

// 所有回复类型的基类
type baseResponse struct {
	Body        []byte
	RawResponse *http.Response
}

type QfResponse[T any] interface {
	*T
	SetResponse(Body []byte, RawResponse *http.Response)
}

func (r *baseResponse) SetResponse(Body []byte, RawResponse *http.Response) {
	r.Body = Body
	r.RawResponse = RawResponse
}

type Requestor struct {
	client  *http.Client
	Options *RequestorOptions
}

type Stream[T any, Ptr QfResponse[T]] struct {
	*streamInternal
}

func (s *Stream[T, Ptr]) Recv() (Ptr, error) {
	response, err := s.streamInternal.Recv()
	var responseBody Ptr = new(T)
	if err != nil {
		return responseBody, err
	}
	responseBody.SetResponse(response.Body, response.RawResponse)
	err = json.Unmarshal(response.Body, &responseBody)
	if err != nil {
		return responseBody, err
	}
	return responseBody, nil
}

type streamInternal struct {
	httpResponse *http.Response
	scanner      *bufio.Scanner
}

func newStreamInternal(httpResponse *http.Response) (*streamInternal, error) {
	return &streamInternal{
		httpResponse: httpResponse,
		scanner:      bufio.NewScanner(httpResponse.Body),
	}, nil
}

func (si *streamInternal) Close() {
	si.httpResponse.Body.Close()
}

func (si *streamInternal) Recv() (*baseResponse, error) {
	var eventData []byte
	for len(eventData) == 0 {
		for {
			if !si.scanner.Scan() {
				return nil, si.scanner.Err()
			}

			line := si.scanner.Bytes()
			if len(line) == 0 {
				break
			}
			var (
				// field []byte = line
				value []byte
			)
			if i := bytes.IndexRune(line, ':'); i != -1 {
				// field = line[:i]
				value = line[i+1:]
				if len(value) != 0 && value[0] == ' ' {
					value = value[1:]
				}
			}
			eventData = append(eventData, value...)
		}
	}
	response := baseResponse{
		Body:        eventData,
		RawResponse: si.httpResponse,
	}
	return &response, nil
}

func newRequestor(options *RequestorOptions) *Requestor {
	return &Requestor{
		client:  &http.Client{},
		Options: options,
	}
}

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
			return fmt.Errorf("unrecognized scheme: %s", u.Scheme)
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

func (r *Requestor) prepareRequest(request *QfRequest) (*http.Request, error) {
	if request.Type == ModelRequest {
		request.URL = GetConfig().BaseURL + request.URL
		request.Body["extra_parameters"] = map[string]string{
			"request_source": VERSION_INDICATOR,
		}
	} else if request.Type == ConsoleRequest {
		request.URL = GetConfig().ConsoleBaseURL + request.URL
		request.Headers["request-source"] = VERSION_INDICATOR
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
	err = r.sign(request)
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

func sendRequest[T any, Ptr QfResponse[T]](requestor *Requestor, request *QfRequest) (Ptr, error) {
	response, err := requestor.request(request)
	if err != nil {
		return nil, err
	}
	var resp Ptr = new(T)
	resp.SetResponse(response.Body, response.RawResponse)
	err = json.Unmarshal(response.Body, resp)
	if err != nil {
		return nil, err
	}
	return resp, nil
}

func (r *Requestor) request(request *QfRequest) (*baseResponse, error) {
	req, err := r.prepareRequest(request)
	if err != nil {
		return nil, err
	}
	resp, err := r.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	response := baseResponse{
		Body:        body,
		RawResponse: resp,
	}

	return &response, nil
}

func sendStreamRequest[T any, Ptr QfResponse[T]](requestor *Requestor, request *QfRequest) (*Stream[T, Ptr], error) {
	stream, err := requestor.requestStream(request)
	if err != nil {
		return nil, err
	}

	return &Stream[T, Ptr]{
		streamInternal: stream,
	}, nil
}

func (r *Requestor) requestStream(request *QfRequest) (*streamInternal, error) {
	req, err := r.prepareRequest(request)
	if err != nil {
		return nil, err
	}
	resp, err := r.client.Do(req)
	if err != nil {
		return nil, err
	}
	stream, err := newStreamInternal(resp)
	if err != nil {
		return nil, err
	}
	return stream, nil
}
