package qianfan

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestConsoleAction(t *testing.T) {
	ca := NewConsoleAction()
	_, err := ca.Call(context.TODO(), "/wenxinworkshop/service/list", "", map[string]interface{}{})
	assert.NoError(t, err)

	// return
	ca1 := NewConsoleAction()
	_, err1 := ca1.Call(context.TODO(), "/v2/service", "DescribeServices", map[string]interface{}{})
	assert.NoError(t, err1)
}
