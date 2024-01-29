# 百度千帆大模型平台 Go SDK

## 如何使用

### 初始化

在使用千帆 SDK 之前，用户需要 [百度智能云控制台 - 安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist) 页面获取 Access Key 与 Secret Key，并在 [千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application) 中创建应用，选择需要启用的服务，具体流程参见平台 [说明文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。在获得了 Access Key 与 Secret Key 后，用户即可开始使用 SDK：

```go
client, err := NewClient("access_key", "secret_key")
client, err := NewClientFromEnv()   // 或者从环境变量中读取

client.Config.AccessKey = "access_key"  // 或者创建变量后再调整设置
```

### Chat 对话

可以调用 `ChatCompletion` 方法进行对话

```go
chat := client.ChatCompletion()  // 使用默认模型 ERNIE-Bot-turbo
// chat := client.ChatCompletionFromModel("ERNIE-Bot-4")  // 可以指定模型
// chat := client.ChatCompletionFromEndpoint("your_custom_endpoint")  // 或者指定 endpoint

resp, err := chat.Do(
    context.Background(), 
    &ChatCompletionRequest{
        Messages: []ChatCompletionMessage{
            ChatCompletionUserMessage("你好"),
        },
    }
)
if err != nil {
    t.Fatal(err)
}
fmt.Printf(resp.Result)   // 模型返回的结果
```

也可以调用 `DoStream` 方法实现流式返回

```go
chat := client.ChatCompletion()

resp, err := chat.DoStream(  // DoStream 启用流式返回，参数与 Do 相同
    context.Background(), 
    &ChatCompletionRequest{
        Messages: []ChatCompletionMessage{
            ChatCompletionUserMessage("你好"),
        },
    }
)
if err != nil {
    t.Fatal(err)
}
defer resp.Close()  // 关闭流
for {
    resp, err := resp.Recv()  // 每次循环可以拿到流式返回的结果
    if err != nil {
        assert.Fail(t, "got err")
    }
    if resp.IsEnd {  // 判断是否是流式返回的结束标志
        break
    }
    fmt.Printf(resp.Result)
}
```