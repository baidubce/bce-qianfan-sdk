package qianfan

import (
	"context"
	"testing"
)

func TestServiceList(t *testing.T) {
	service := NewService()
	resp, err := service.List(
		context.TODO(),
		&ServiceListRequest{},
	)
	if err != nil {
		t.Error(err)
	}
	print(resp)
}
