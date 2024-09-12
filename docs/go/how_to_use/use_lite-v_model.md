# 在千帆 Go SDK 中使用 Lite-V 模型

Lite-V 模型是百度针对多模态场景打造的一款模型。本文将介绍如何在千帆 Go SDK 中使用 Lite-V 模型。

# 0. 准备工作

为了使用 Lite-V 模型，我们需要：

a. 安装千帆 Go SDK 和百度智能云 Bos SDK

```shell
go get github.com/baidubce/bce-qianfan-sdk/go/qianfan
go get github.com/baidubce/bce-sdk-go/services/bos
```

b. 导入相关包

```go
import (
	"context"
	"encoding/json"
	"fmt"
	"image"
	_ "image/jpeg"
	"os"
	
	"github.com/baidubce/bce-qianfan-sdk/go/qianfan"
	"github.com/baidubce/bce-sdk-go/services/bos"
)
```

c. 设置好百度智能云的 Access Key 和 Secret Key 以及相关环境变量

Go：
```
var (
    ak              = "" // 百度智能云的 Access Key
    sk              = "" // 百度智能云的 Secret Key
    bucket          = "" // 存储图片的 BOS Bucket
    bucketImagePath = "" // BOS Bucket 中的图片路径
    localImagePath  = "" // 本地图片的路径
)
```

Shell:
```shell
export QIANFAN_ACCESS_KEY=""
export QIANFAN_SECRET_KEY=""
```

# 1. 初始化

我们需要先初始化好所需要使用到的千帆 SDK 和 Bos SDK 客户端对象

```
qianfanClient := qianfan.NewBaseModel()
bosClient, err := bos.NewClient(ak, sk, "")
if err != nil {
    panic(err)
}
```

# 2. 读取图片并上传到 BOS

为了使用 Lite-V 模型的多模态功能，我们需要将其上传到可被访问的服务之中。并且使用传递 URL 的方式来让 Lite-V 模型来读取该图片

```go
imageFile, err := os.Open(localImagePath)
if err != nil {
    panic(err)
}
defer imageFile.Close()

imageConfig, _, err := image.DecodeConfig(imageFile)
if err != nil {
    panic(err)
}

imageHeight := imageConfig.Height
imageWidth := imageConfig.Width

if _, err = bosClient.PutObjectFromFile(bucket, bucketImagePath, localImagePath, nil); err != nil {
    panic(err)
}

url := bosClient.BasicGeneratePresignedUrl(bucket, bucketImagePath, 120)
```

# 3. 请求 Lite-V 模型

我们可以使用千帆 Go SDK 提供的接口来自行拼接请求参数，实现对 Lite-V 模型的灵活请求，以上面的图片举例：

```
request, _ := qianfan.NewModelRequest(
    "POST",
    "/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-lite-v",
    qianfan.RawRequest{
        "messages": []map[string]any{
            {
                "role": "user",
                "content": []map[string]any{
                    {
                        "type": "image_url",
                        "image_url": map[string]any{
                            "image_width":  imageWidth,
                            "image_height": imageHeight,
                            "url":          url,
                        },
                    },
                    {
                        "type": "text",
                        "text": "这个图片展示了什么",
                    },
                },
            },
        },
    },
)
```

# 4. 发送请求并获取结果

在使用 `BaseModel` 调用 `Do` 进行请求时，返回值是一个代表了响应结果的 `RawResponse` 对象。用户可以使用 `json.Unmarshal` 方法将响应结果反序列化为一个 `map[string]any` 对象，方便后续处理

```
resp, err := qianfanClient.Do(context.Background(), request)
if err != nil {
    fmt.Println(err)
} else {
    result := make(map[string]any)
    json.Unmarshal(resp.Body, &result)
    fmt.Println(result)
}
```

