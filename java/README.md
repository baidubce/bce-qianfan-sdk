# 百度千帆大模型平台 Java SDK

## 安装

> 使用千帆JavaSDK，需要Java版本>=8

### Maven

在pom.xml的dependencies中添加依赖

```xml
<dependency>
    <groupId>com.baidubce</groupId>
    <artifactId>qianfan</artifactId>
    <version>0.0.1</version>
</dependency>
```

### Gradle

对于Kotlin DSL，在build.gradle.kts的dependencies中添加依赖

```kotlin
implementation("com.baidubce:qianfan:0.0.1")
```

对于Groovy DSL，在build.gradle的dependencies中添加依赖

```groovy
implementation 'com.baidubce:qianfan:0.0.1'
```

> 我们提供了一些 [示例](./examples)，可以帮助快速了解 SDK 的使用方法并完成常见功能。

## 如何使用

### 鉴权

在使用千帆 SDK 之前，用户需要 [百度智能云控制台 - 安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist) 页面获取 Access Key 与 Secret Key，并在 [千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application) 中创建应用，选择需要启用的服务，具体流程参见平台 [说明文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

SDK 支持从环境变量 `QIANFAN_ACCESS_KEY` 和 `QIANFAN_SECRET_KEY` 获取配置，这一步骤会在使用 SDK 时自动完成。

```bash
export QIANFAN_ACCESS_KEY=your_access_key
export QIANFAN_SECRET_KEY=your_secret_key
```

同时，也可以在代码中实例化Qianfan时手动传入 `AccessKey` 和 `SecretKey`，具体如下：

```java
Qianfan qianfan = new Qianfan("your_access_key", "your_secret_key");
```

#### 其他鉴权方式

API Key (**AK**) 和 Secret Key (**SK**）是用户在调用千帆模型相关功能时所需要的凭证。具体获取流程参见平台的[应用接入使用说明文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake)，但该认证方式无法使用训练、发布模型等功能，若需使用请使用 Access Key 和 Secret Key 的方式进行认证。在获得并配置了 AK 以及 SK 后，用户即可开始使用 SDK，可以通过环境变量的方式配置。

```bash
export QIANFAN_AK=your_ak
export QIANFAN_SK=your_sk
```

也可以在代码中通过如下方式配置

```java
Qianfan qianfan = new Qianfan(Auth.TYPE_OAUTH, "your_ak", "your_sk");
```

### Chat 对话

可以使用 `chatCompletion` 方法完成对话相关操作，在调用`Qianfan`的`chatCompletion`方法会返回一个`ChatBuilder`，以便通过链式调用的方式构造请求，在请求的参数设置完毕后，可以调用`execute`方法发起请求，并返回`ChatResponse`。

示例如下：

```java
ChatResponse response = new Qianfan().chatCompletion()
        .model("ERNIE-Bot-4") // 使用model指定预置模型
        // .endpoint("completions_pro") // 也可以使用endpoint指定任意模型 (二选一)
        .addMessage("user", "你好") // 添加用户消息 (此方法可以调用多次，以实现多轮对话的消息传递)
        .temperature(0.7) // 自定义超参数
        .execute(); // 发起请求
System.out.println(response.getResult());
```

也可以调用 `executeStream` 方法发起流式请求，会返回`Iterator<ChatResponse>`，即`ChatResponse`的迭代器，通过`hasNext`检查是否有新的消息片段，并通过`next`获取下一个消息片段。

示例如下：

```java
new Qianfan().chatCompletion()
        .model("ERNIE-Bot-4")
        .addMessage("user", "你好")
        .executeStream() // 发起流式请求
        .forEachRemaining(chunk -> System.out.print(chunk.getResult())); // 流式迭代，并打印消息
```

### Completion 续写

对于不需要多轮对话，仅需要根据prompt进行补全的场景来说，用户可以使用 `completion` 来完成这一任务。

```java
CompletionResponse response = new Qianfan().completion()
        .model("CodeLlama-7b-Instruct")
        // 与Chat类似，但通过prompt传入指令
        .prompt("hello")
        .execute();
System.out.println(response.getResult());
```

也可以调用 `executeStream` 方法实现流式返回

```java
Iterator<CompletionResponse> response = new Qianfan().completion()
        .model("CodeLlama-7b-Instruct")
        .prompt("hello")
        .executeStream();
while (response.hasNext()) {
    System.out.print(response.next().getResult());
}
```

### Embedding 向量化

千帆 SDK 同样支持调用千帆大模型平台中的模型，将输入文本转化为用浮点数表示的向量形式。转化得到的语义向量可应用于文本检索、信息推荐、知识挖掘等场景。

```java
List<String> inputs = new ArrayList<>();
inputs.add("今天的晚饭好吃吗");
inputs.add("今日晚餐味道咋样");

EmbeddingResponse response = new Qianfan().embedding()
        // 指定embedding模型
        .model("Embedding-V1")
        .input(inputs)
        .execute();
response.getData().forEach(data -> {
    System.out.println(inputs.get(data.getIndex()));
    System.out.println(data.getEmbedding());
});
```

### 文生图

千帆 SDK 支持调用文生图模型，将输入文本转化为图片。

```java
Text2ImageResponse response = new Qianfan().text2Image()
        .prompt("cute cat")
        .execute();
System.out.println(response.getData().get(0).getB64Image());
```

### 图像理解

千帆 SDK 支持调用图像理解模型，用于根据用户输入的图像和文字，回答图像有关问题。

```java
Image2TextResponse response = new Qianfan().image2Text()
        .image("9j/4AAQSkZJRgABAQAAAQABAAD/xxxxx")
        .prompt("introduce the picture")
        .execute();
System.out.println(response.getResult());
```
