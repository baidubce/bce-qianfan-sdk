package qianfan

import (
	"context"
	"strconv"
)

type consoleBase struct {
	*Requestor
}

type ConsoleAPIError struct {
	ErrorCode int    `json:"error_code"` // 错误码
	ErrorMsg  string `json:"error_msg"`  // 错误消息
}

type ConsoleResponse struct {
	LogID   string `json:"log_id"`
	Success bool   `json:"success"`
	ConsoleAPIError
	baseResponse
}

type ConsoleAPIResponse interface {
	GetError() (int, string)
}

// 获取错误码和错误信息
func (e *ConsoleAPIError) GetError() (int, string) {
	return e.ErrorCode, e.ErrorMsg
}

// 获取错误码
func (e *ConsoleAPIError) GetErrorCode() string {
	return strconv.Itoa(e.ErrorCode)
}

func (c *consoleBase) requestResource(ctx context.Context, request *QfRequest, response any) error {
	qfResponse, ok := response.(QfResponse)
	if !ok {
		return &InternalError{Msg: "response is not QfResponse"}
	}
	consoleResponse, ok := response.(ConsoleAPIResponse)
	if !ok {
		return &InternalError{Msg: "response is not ConsoleAPIResponse"}
	}

	requestFunc := func() error {
		err := c.Requestor.request(ctx, request, qfResponse)
		if err != nil {
			resp := qfResponse.GetResponse()
			if resp != nil {
				// 可能是 IAM 错误
				errCode := resp.Header.Get("X-Bce-Error-Code")
				if errCode != "" {
					return &IAMError{
						Code: errCode,
						Msg:  resp.Header.Get("X-Bce-Error-Message"),
					}
				}
			}
			return nil
		}
		errCode, errMsg := consoleResponse.GetError()
		if errCode != 0 {
			return &APIError{Code: errCode, Msg: errMsg}
		}
		return nil
	}
	return requestFunc()
}
