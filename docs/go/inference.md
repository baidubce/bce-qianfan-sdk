# 大模型推理
 
## Chat 对话

用户只需要提供预期使用的模型名称和对话内容，即可调用千帆大模型平台支持的，包括 ERNIE 系列在内的所有预置模型，如下所示：

```go
chat := qianfan.NewChatCompletion() 

// 调用默认模型，即 ERNIE-Lite-8K
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
// 输出：你好！有什么我可以帮助你的吗？

// 指定特定模型
chat := qianfan.NewChatCompletion(
    qianfan.WithModel("ERNIE-4.0-8K"),  // 支持的模型可以通过 chat.ModelList() 获取
)
// 或者通过 WithEndpoint 指定自行发布的模型
chat := qianfan.NewChatCompletion(
    qianfan.WithEndpoint("your_custom_endpoint"),
)
```

目前，千帆大模型平台提供了一系列可供用户通过 SDK 直接使用的模型，模型清单如下所示：

- [ERNIE-4.0-8K](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clntwmv7t)
- [ERNIE-3.5-8K](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/jlil56u11)
- [ERNIE-3.5-4K-0205](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Llsr67q8h)
- [ERNIE-3.5-8K-0205](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/llsr6hjxo)
- [ERNIE-3.5-8K-1222](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mlt3vdi2j)
- [ERNIE-Speed-8K](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/klqx7b1xf)
- [ERNIE-Lite-8K](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/dltgsna1o) （默认）
- [BLOOMZ-7B](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Jljcadglj)
- [Llama-2-7b-chat](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Rlki1zlai)
- [Llama-2-13b-chat](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lki2us1e)
- [Llama-2-70b-chat](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/8lkjfhiyt)
- [Qianfan-BLOOMZ-7B-compressed](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/nllyzpcmp)
- [Qianfan-Chinese-Llama-2-7B](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Sllyztytp)
- [Qianfan-Chinese-Llama-2-13B](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/8lo479b4b)
- [ChatGLM2-6B-32K](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Bllz001ff)
- [AquilaChat-7B](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ollz02e7i)
- [XuanYuan-70B-Chat-4bit](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Ylp88e5jc)
- [ChatLaw](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Qlphtigbf)
- [Mixtral-8x7B-Instruct](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Rlqx7c834)
- [Yi-34B-Chat](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/vlpteyv3c)

支持的预置模型列表可以通过 `qianfan.NewChatCompletion().models()` 获得。

对于那些不在清单中的其他模型，用户可通过传入 `WithEndpoint("your_endpoint")` 选项来使用它们。

除了通过  `Do`  方法同步调用千帆 SDK 以外， 用户还可以使用 `Stream()` 来实现大模型输出结果的流式返回。示例代码如下所示：

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

## Completion 续写

对于不需要对话，仅需要根据 prompt 进行补全的场景来说，用户可以使用 `Completion` 来完成这一任务。

```go
completion := qianfan.NewCompletion()  // 不传入使用默认模型

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

目前，平台预置的续写模型有：

- [SQLCoder-7B](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlo472sa2)
- [CodeLlama-7b-Instruct](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ylo47d03k)

同时 SDK 也支持传入对话类模型实现续写任务。

## Embedding 向量化

千帆 SDK 同样支持调用千帆大模型平台中的模型，将输入文本转化为用浮点数表示的向量形式。转化得到的语义向量可应用于文本检索、信息推荐、知识挖掘等场景。

```go
embed := qianfan.NewEmbedding()  // 默认使用 Embedding-V1 模型

// 可以通过 WithModel 指定模型
embed := qianfan.NewEmbedding(
    qianfan.WithModel("ERNIE-4.0-8K"),  // 支持的模型可以通过 embed.ModelList() 获取
)
// 或者通过 WithEndpoint 指定 endpoint
embed := qianfan.NewEmbedding(
    qianfan.WithEndpoint("your_custom_endpoint"),
)
```

对于向量化任务，目前千帆大模型平台预置的模型有：

- [Embedding-V1](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/alj562vvu) （默认）
- [bge-large-en](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mllz05nzk)
- [bge-large-zh](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/dllz04sro)

