package qianfan

import (
	"net/http"
)

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

type baseResponse struct {
	Body        []byte
	RawResponse *http.Response
}

type Ptr[T any] interface {
	*T
}

type QfResponse[T any] interface {
	*T
	SetResponse(Body []byte, RawResponse *http.Response)
}

func (r *baseResponse) SetResponse(Body []byte, RawResponse *http.Response) {
	r.Body = Body
	r.RawResponse = RawResponse
}
