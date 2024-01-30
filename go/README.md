# 百度千帆大模型平台 Go SDK

## 如何使用

首先可以通过如下命令安装 SDK：

```
go get github.com/baidubce/bce-qianfan-sdk/go/qianfan
```

之后就可以在代码中通过如下方式引入 SDK：

```
import (
	"github.com/baidubce/bce-qianfan-sdk/go/qianfan"
)
```

### 鉴权

在使用千帆 SDK 之前，用户需要 [百度智能云控制台 - 安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist) 页面获取 Access Key 与 Secret Key，并在 [千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application) 中创建应用，选择需要启用的服务，具体流程参见平台 [说明文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

SDK 支持从当前目录的 `.env` 中读取配置，也可以通过环境变量 `QIANFAN_ACCESS_KEY` 和 `QIANFAN_SECRET_KEY` 获取配置，这一步骤会在使用 SDK 时自动完成。

```bash
export QIANFAN_ACCESS_KEY=your_access_key
export QIANFAN_SECRET_KEY=your_secret_key
```

同时，也可以在代码中手动设置 `AccessKey` 和 `SecretKey`，具体如下：

```go
qianfan.GetConfig().AccessKey = "your_access_key"
qianfan.GetConfig().SecretKey = "your_secret_key"
```

### Chat 对话

可以使用 `ChatCompletion` 对象完成对话相关操作，可以通过如下方法获取一个 `ChatCompletion` 对象：

```go
chat := qianfan.NewChatCompletion()  // 默认使用 ERNIE-Bot-turbo 模型

// 可以通过 WithModel 指定模型
chat := qianfan.NewChatCompletion(
    qianfan.WithModel("ERNIE-Bot-4"),  // 支持的模型可以通过 chat.ModelList() 获取
)
// 或者通过 WithEndpoint 指定 endpoint
chat := qianfan.NewChatCompletion(
    qianfan.WithEndpoint("your_custom_endpoint"),
)
```

之后就可以通过 `Do` 方法进行对话：

```
resp, err := chat.Do(
    context.TODO(),
    &qianfan.ChatCompletionRequest{
        Messages: []qianfan.ChatCompletionMessage{
            qianfan.ChatCompletionUserMessage("你好"),
        },
    },
)
if err != nil {
    fmt.Print(err)
}
fmt.Print(resp.Result)
```

也可以调用 `Stream` 方法实现流式返回

```go
chat := client.ChatCompletion()

resp, err := chat.Stream(  // Stream 启用流式返回，参数与 Do 相同
    context.TODO(),
    &qianfan.ChatCompletionRequest{
        Messages: []qianfan.ChatCompletionMessage{
            qianfan.ChatCompletionUserMessage("你好"),
        },
    },
)
if err != nil {
    return err
}
defer resp.Close()  // 关闭流
for {
    r, err := resp.Recv()
    if err != nil {
        return err
    }
    if resp.IsEnd { // 判断是否结束
        break
    }
    fmt.Print(r.Result)
}
```

### Completion 续写

对于不需要对话，仅需要根据 prompt 进行补全的场景来说，用户可以使用 `Completion` 来完成这一任务。

```go
completion := qianfan.NewCompletion()  // 默认使用 ERNIE-Bot-turbo 模型

// 可以通过 WithModel 指定模型
completion := qianfan.NewCompletion(
    qianfan.WithModel("ERNIE-Bot-4"),  
    // 支持的模型可以通过 completion.ModelList() 获取
)
// 或者通过 WithEndpoint 指定 endpoint
completion := qianfan.NewCompletion(
    qianfan.WithEndpoint("your_custom_endpoint"),
)
```

与对话相同，可以调用 `Do` 方法实现续写

```go
resp, err := completion.Do(
    context.Background(), 
    &CompletionRequest{
        Prompt: prompt,
    }
)
if err != nil {
    return err
}
fmt.Printf(resp.Result)   // 模型返回的结果
```

也可以调用 `Stream` 方法实现流式返回

```go
resp, err := completion.Stream(  // Stream 启用流式返回，参数与 Do 相同
    context.Background(), 
    &CompletionRequest{
        Prompt: prompt,
    }
)
if err != nil {
    return err
}
defer resp.Close()  // 关闭流
for {
    r, err := resp.Recv()
    if err != nil {
        return err
    }
    if resp.IsEnd { // 判断是否结束
        break
    }
    fmt.Print(r.Result)
}
```

### Embedding 向量化

千帆 SDK 同样支持调用千帆大模型平台中的模型，将输入文本转化为用浮点数表示的向量形式。转化得到的语义向量可应用于文本检索、信息推荐、知识挖掘等场景。

```go
embed := qianfan.NewEmbedding()  // 默认使用 Embedding-V1 模型

// 可以通过 WithModel 指定模型
embed := qianfan.NewEmbedding(
    qianfan.WithModel("ERNIE-Bot-4"),  // 支持的模型可以通过 embed.ModelList() 获取
)
// 或者通过 WithEndpoint 指定 endpoint
embed := qianfan.NewEmbedding(
    qianfan.WithEndpoint("your_custom_endpoint"),
)
```

之后使用 `Do` 方法进行调用

```go
resp, err := embed.Do(
    context.Background(), 
    &EmbeddingRequest{
        Input: []string{"hello1", "hello2"},
    }
)
if err != nil {
    return err
}
embed := resp.Data[0].Embedding  // 获取第一个输入的向量
```
