# 其他设置

为了便于使用，SDK 提供了一些设置项。

## 超时重试

为了避免因 QPS 限制等原因导致请求失败，SDK 提供了超时重试功能，可以通过如下方式设置

```go
qianfan.GetConfig().LLMRetryCount = 3          // 最多尝试 3 次，默认为 1，若设置为 0 则无限重试
qianfan.GetConfig().LLMRetryTimeout = 60       // 请求的超时时间，默认为 0 即不设置
qianfan.GetConfig().LLMRetryBackoffFactor = 1  // 指数回避因子，默认为 0
```

也可以单独为某个实例设置

```go
chat := qianfan.NewChatCompletion(  // Completion 与 Embedding 可以用同样方式设置
    WithLLMRetryCount(3),           // 最多重试 3 次
    WithLLMRetryTimeout(60),        // 超时 60s
    WithLLMRetryBackoffFactor(1),   // 指数回避因子
)
```