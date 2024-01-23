package qianfan

import "net/http"

type QfRequest struct {
	Method  string
	URL     string
	Headers map[string]string
	Params  map[string]string
	Body    interface{}
}

type QfResponse struct {
	Body        []byte
	RawResponse *http.Response
}
