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

> 我们提供了一些 [示例](./examples)，可以帮助快速了解 SDK 的使用方法并完成常见功能。

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

<details>
<summary> 其他认证方式 </summary>

> 这里是一些其他认证方式，请仅在无法获取 Access Key 与 Secret Key 时使用。这些认证方式已经过时，将在未来从 SDK 中移除。

API Key (**AK**) 和 Secret Key (**SK**）是用户在调用千帆模型相关功能时所需要的凭证。具体获取流程参见平台的[应用接入使用说明文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake)，但该认证方式无法使用训练、发布模型等功能，若需使用请使用 Access Key 和 Secret Key 的方式进行认证。在获得并配置了 AK 以及 SK 后，用户即可开始使用 SDK，可以通过环境变量的方式配置

```bash
export QIANFAN_AK=your_ak
export QIANFAN_SK=your_sk
```

也可以在代码中通过如下方式配置

```go
qianfan.GetConfig().AK = "your_ak"
qianfan.GetConfig().SK = "your_sk"
```

</details>

### Chat 对话

可以使用 `ChatCompletion` 对象完成对话相关操作，可以通过如下方法获取一个 `ChatCompletion` 对象：

```go
chat := qianfan.NewChatCompletion()  // 使用默认模型

// 可以通过 WithModel 指定模型
chat := qianfan.NewChatCompletion(
    qianfan.WithModel("ERNIE-4.0-8K"),  // 支持的模型可以通过 chat.ModelList() 获取
)
// 或者通过 WithEndpoint 指定 endpoint
chat := qianfan.NewChatCompletion(
    qianfan.WithEndpoint("your_custom_endpoint"),
)
```

之后就可以通过 `Do` 方法进行对话：

```go
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
completion := qianfan.NewCompletion()  // 使用默认模型

// 可以通过 WithModel 指定模型
completion := qianfan.NewCompletion(
    qianfan.WithModel("ERNIE-4.0-8K"),  
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
    context.TODO(), 
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
    context.TODO(), 
    &CompletionRequest{
        Prompt: prompt,
    }
)
if err != nil {
    return err
}
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
    qianfan.WithModel("Embedding-V1"),  // 支持的模型可以通过 embed.ModelList() 获取
)
// 或者通过 WithEndpoint 指定 endpoint
embed := qianfan.NewEmbedding(
    qianfan.WithEndpoint("your_custom_endpoint"),
)
```

之后使用 `Do` 方法进行调用

```go
resp, err := embed.Do(
    context.TODO(), 
    &EmbeddingRequest{
        Input: []string{"hello1", "hello2"},
    }
)
if err != nil {
    return err
}
embed := resp.Data[0].Embedding  // 获取第一个输入的向量
```

### Text2Image 文生图

千帆 SDK 支持调用千帆大模型平台中的文生图模型，可快速生成图片。

```go
text2img := qianfan.NewText2Image()  // 默认使用 Stable-Diffusion-XL 模型

// 可以通过 WithModel 指定模型
text2img := qianfan.NewText2Image(
    qianfan.WithModel("Stable-Diffusion-XL"),  // 支持的模型可以通过 text2img.ModelList() 获取
)
// 或者通过 WithEndpoint 指定 endpoint
text2img := qianfan.NewText2Image(
    qianfan.WithEndpoint("your_custom_endpoint"),
)
```

之后使用 `Do` 方法进行调用

```go
resp, err := text2img.Do(
    context.TODO(), 
    &Text2ImageRequest{
        Prompt: "target prompt",
    }
)
if err != nil {
    return err
}
image := resp.Data[0].Base64Image  // 获取输出的第一张图片的 base64 编码
```

### 其他设置

为了便于使用，SDK 提供了一些设置项。

#### 重试

为了避免因 QPS 限制等原因导致请求失败，SDK 提供了重试功能，可以通过如下方式设置

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

同时，由于只有部分错误可以通过重试解决，SDK 只会对部分错误码进行重试，可以通过如下方式自定义修改

```go
qianfan.GetConfig().RetryErrCodes = []int{
    // 以下是 SDK 默认重试的错误码
    qianfan.ServiceUnavailableErrCode,  // 2
    qianfan.ServerHighLoadErrCode,      // 336100
    qianfan.QPSLimitReachedErrCode,     // 18
    qianfan.RPMLimitReachedErrCode,     // 336501
    qianfan.TPMLimitReachedErrCode,     // 336502
    qianfan.AppNotExistErrCode,         // 15
    // 以下为非内置错误码，仅为示例如何增加自定义错误码
    qianfan.UnknownErrorErrCode,
    // 也可以直接提供 int 类型的错误码
    336000,
}
```
