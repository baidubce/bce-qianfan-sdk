# 在千帆 Go SDK 中使用插件

# 0. 准备工作

为了使用插件功能，我们需要：

a. 安装千帆 Go SDK

```shell
go get github.com/baidubce/bce-qianfan-sdk/go/qianfan
```

b. 导入相关包

```go
import (
	"github.com/baidubce/bce-qianfan-sdk/go/qianfan"
)
```

c. 设置好百度智能云的 Access Key 和 Secret Key

```shell
export QIANFAN_ACCESS_KEY=""
export QIANFAN_SECRET_KEY=""
```

# 1. 初始化

我们需要先初始化好所需要使用到的千帆 SDK 对象

```
qianfanClient := qianfan.NewBaseModel()
```

# 2. 构造插件请求

我们可以使用千帆 Go SDK 提供的接口来自行拼接请求参数，以使用 `ChatFilePlus` 插件为例：

```
request, _ := qianfan.NewModelRequest(
    "POST",
    "/rpc/2.0/ai_custom/v1/wenxinworkshop/erniebot/plugin",
    qianfan.RawRequest{
        "messages": []map[string]any{
            {
                "role":    "user",
                "content": `['\''牛奶的营养成本有哪些<file>浅谈牛奶的营养与消费趋势.docx</file><url>https://qianfan-doc.bj.bcebos.com/chatfile/%E6%B5%85%E8%B0%88%E7%89%9B%E5%A5%B6%E7%9A%84%E8%90%A5%E5%85%BB%E4%B8%8E%E6%B6%88%E8%B4%B9%E8%B6%8B%E5%8A%BF.docx</url>'\'']`,
            },
        },
        "plugins": []string{
            "ChatFilePlus",
        },
    },
)
```

# 3. 发送请求并获取结果

在使用 `BaseModel` 调用 `Stream` 进行请求时，返回值是一个代表了流式响应迭代器的 `RawModelResponseStream` 对象。用户可以使用 `Recv` 方法来获取每次流式返回的 `RawResponse` 对象

```
stream, err := qianfanClient.Stream(context.Background(), request)
if err != nil {
    fmt.Println(err)
} else {
    for {
        resp, err := stream.Recv()
        if err != nil {
            fmt.Println(err)
            break
        } else {
            result := make(map[string]any)
            json.Unmarshal(resp.Body, &result)
            str, _ := json.Marshal(result)
            fmt.Println(string(str))
            if end, ok := result["is_end"].(bool); ok && end {
                break
            }
        }
    }
}
```

