# 百度千帆大模型平台 Go SDK

## 如何使用

对话

```go
client, err := NewClientFromEnv()
if err != nil {
    t.Fatal(err)
}
chat := client.ChatCompletion()
resp, err := chat.Do(context.Background(), &ChatCompletionRequest{
    Messages: []ChatCompletionMessage{
        ChatCompletionUserMessage("你好"),
    },
})
if err != nil {
    t.Fatal(err)
}
fmt.Printf(resp.Result)
```

流式

```go
client, err := NewClientFromEnv()
if err != nil {
    t.Fatal(err)
}
chat := client.ChatCompletion()
resp, err := chat.DoStream(context.Background(), &ChatCompletionRequest{
    Messages: []ChatCompletionMessage{
        ChatCompletionUserMessage("你好"),
    },
})
if err != nil {
    t.Fatal(err)
}
defer resp.Close()
for {
    resp, err := resp.Recv()
    if err != nil {
        assert.Fail(t, "got err")
    }
    if resp.IsEnd {
        break
    }
    fmt.Printf(resp.Result)
}
```