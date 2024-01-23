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

func makeRequest(method string, url string, body Mappable) (*QfRequest, error) {
	b, err := body.toMap()
	if err != nil {
		return nil, err
	}
	return &QfRequest{
		Method:  method,
		URL:     url,
		Body:    b,
		Params:  map[string]string{},
		Headers: map[string]string{},
	}, nil
}

type QfResponse struct {
	Body        []byte
	RawResponse *http.Response
}
