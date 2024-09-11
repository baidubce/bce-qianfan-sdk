package qianfan

import (
	"context"
	"fmt"
)

type ConsoleAction struct {
	consoleBase
}

func NewConsoleAction(optionList ...Option) *ConsoleAction {
	options := makeOptions(optionList...)
	return &ConsoleAction{
		consoleBase: consoleBase{
			Requestor: newRequestor(options),
		},
	}
}

func (ca *ConsoleAction) baseActionUrl(route, action string) string {
	if action == "" {
		return route
	} else {
		return fmt.Sprintf("%v?Action=%v", route, action)
	}
}

func (ca *ConsoleAction) Call(ctx context.Context, route string, action string, params map[string]interface{}) (*ConsoleResponse, error) {
	reqBody := BaseRequestBody{
		Extra: params,
	}
	req, err := NewConsoleRequest("POST", ca.baseActionUrl(route, action), &reqBody)
	if err != nil {
		logger.Error("new console req error", err)
		return nil, err
	}
	logger.Trace("console req", req)
	resp := &ConsoleResponse{}
	err = ca.requestResource(ctx, req, resp)
	if err != nil {
		logger.Error("request resource failed", err)
		return nil, err
	}
	return resp, nil
}
