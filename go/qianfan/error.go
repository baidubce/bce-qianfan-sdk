package qianfan

import "fmt"

// 模型不被支持，请使用 `ModelList()` 获取支持的模型列表
type ModelNotSupportedError struct {
	Model string
}

func (e *ModelNotSupportedError) Error() string {
	return fmt.Sprintf("model `%s` is not supported, use `ModelList()` to acquire supported model list", e.Model)
}

type APIError struct {
	Code int
	Msg  string
}

func (e *APIError) Error() string {
	return fmt.Sprintf("api error, code: %d, msg: %s", e.Code, e.Msg)
}

type CredentialNotFoundError struct {
}

func (e *CredentialNotFoundError) Error() string {
	return "no enough credentails found. Please set AK and SK or AccessKey and SecretKey"
}
