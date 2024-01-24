package qianfan

import (
	"net/http"
)

type Mappable interface {
	toMap() (map[string]interface{}, error)
}

type BaseRequestBody struct {
	Extra map[string]interface{} `mapstructure:"-"`
}

func (r *BaseRequestBody) SetExtra(m map[string]interface{}) {
	r.Extra = m
}

func (r *BaseRequestBody) toMap() (map[string]interface{}, error) {
	return r.Extra, nil
}

func (r *BaseRequestBody) union(m map[string]interface{}) (map[string]interface{}, error) {
	for k, v := range r.Extra {
		m[k] = v
	}
	return m, nil
}

type QfRequest struct {
	Method  string
	URL     string
	Headers map[string]string
	Params  map[string]string
	Body    map[string]interface{}
}

func newRequest(method string, url string, body Mappable) (*QfRequest, error) {
	b, err := body.toMap()
	if err != nil {
		return nil, err
	}
	return newRequestFromMap(method, url, b)
}

func newRequestFromMap(method string, url string, body map[string]interface{}) (*QfRequest, error) {
	return &QfRequest{
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

type QfResponse interface {
	SetResponse(Body []byte, RawResponse *http.Response)
}

type QfResponsePtr[T any] interface {
	*T
	QfResponse
}

func (r *baseResponse) SetResponse(Body []byte, RawResponse *http.Response) {
	r.Body = Body
	r.RawResponse = RawResponse
}
