package qianfan

import (
	"context"
	"errors"
	"strings"
	"unicode"
)

type ebTokenizerRequest struct {
	BaseRequestBody `mapstructure:"-"`
	Prompt          string
	Model           string
}

// ErrInternal 定义错误类型
var (
	ErrInternal = errors.New("internal error")
)

// Tokenizer 结构体
type Tokenizer struct {
	BaseModel
}

type TokenizerMode string

// TokenizerMode 枚举
const (
	TokenizerModeLocal  = TokenizerMode("local")
	TokenizerModeRemote = TokenizerMode("remote")
)

// NewTokenizer 创建 Tokenizer 实例
func NewTokenizer() *Tokenizer {
	return &Tokenizer{}
}

// CountTokens 计算给定文本中的 token 数量
func (t *Tokenizer) CountTokens(text string, mode TokenizerMode, model string, additionalArguments map[string]interface{}) (int, error) {
	if mode == TokenizerModeLocal {
		return t.localCountTokens(text, additionalArguments)
	}

	if mode == TokenizerModeRemote {
		return t.remoteCountTokensEB(text, model)
	}

	return 0, ErrInternal
}

// localCountTokens 本地计算 token 数量
func (t *Tokenizer) localCountTokens(text string, additionalArguments map[string]interface{}) (int, error) {
	hanTokens := 0.625
	wordTokens := 1.0

	// 从 additionalArguments 中获取 hanTokens 和 wordTokens 的值
	if val, ok := additionalArguments["han_tokens"].(float64); ok {
		hanTokens = val
	}
	if val, ok := additionalArguments["word_tokens"].(float64); ok {
		wordTokens = val
	}

	hanCount := 0
	textOnlyWord := ""

	for _, ch := range text {
		if isCJKCharacter(ch) {
			hanCount++
			textOnlyWord += " "
		} else if isPunctuation(ch) || isSpace(ch) {
			textOnlyWord += " "
		} else {
			textOnlyWord += string(ch)
		}
	}

	wordCount := len(strings.Fields(textOnlyWord))
	return int(float64(hanCount)*hanTokens + float64(wordCount)*wordTokens), nil
}

// remoteCountTokensEB 调用 API 获取 token 数量
func (t *Tokenizer) remoteCountTokensEB(text string, model string) (int, error) {
	request := &ebTokenizerRequest{
		Prompt: text,
		Model:  model,
	}

	req, err := NewModelRequest("POST", modelAPIPrefix+"/tokenizer/erniebot", request)
	if err != nil {
		return -1, err
	}

	var resp ModelResponse

	err = t.requestResource(context.Background(), req, &resp)
	if err != nil {
		return -1, err
	}
	return resp.Usage.TotalTokens, nil
}

// isCJKCharacter 检查字符是否是 CJK 字符
func isCJKCharacter(ch rune) bool {
	return unicode.Is(unicode.Han, ch)
}

// isSpace 检查字符是否是空格
func isSpace(ch rune) bool {
	return unicode.IsSpace(ch)
}

// isPunctuation 检查字符是否是标点符号
func isPunctuation(ch rune) bool {
	return unicode.IsPunct(ch)
}
