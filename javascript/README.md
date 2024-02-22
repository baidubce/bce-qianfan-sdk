# 百度千帆大模型平台 Go SDK

## 如何使用

首先可以通过如下命令安装 SDK：

```sh
npm install @baiducloud/qianfan-sdk
# or
yarn add @baiducloud/qianfan-sdk
```

### 鉴权

在使用千帆 SDK 之前，用户需要 [百度智能云控制台 - 安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist) 页面获取 Access Key 与 Secret Key，并在 [千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application) 中创建应用，选择需要启用的服务，具体流程参见平台 [说明文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

env 读取
```ts
const API_KEY = process.env.API_KEY || '';
const SECRET_KEY = process.env.SECRET_KEY || '';
const IAM_ACESS_KEY = process.env.IAM_ACESS_KEY || '';
const IAM_SECRET_KEY = process.env.IAM_SECRET_KEY || '';
```
默认IAM认证方式，如果使用AK/SK方式鉴权，需要传入Type参数, 参数值如下：'AK'  
```ts
// AK/SK    
 const client = new  ChatCompletion(API_KEY, SECRET_KEY, 'AK');
// IAM 
const client = new ChatCompletion(IAM_ACESS_KEY, IAM_SECRET_KEY);

// TO DO！！！
// 下期优化支持env和手动传入
```
### Chat 对话

可以使用 `ChatCompletion` 对象完成对话相关操作

```ts
import {ChatCompletion} from "@baiducloud/qianfan-sdk";
// AK/SK 测试
const client = new  ChatCompletion(QIANFAN_AK, QIANFAN_SK, 'AK');
// IAM 测试
// const client = new ChatCompletion(QIANFAN_ACCESS_KEY, QIANFAN_SECRET_KEY);
async function main() {
    const resp = await client.chat({
        messages: [
            {
                role: "user",
                content: "今天深圳天气",
            },
        ],
    }, "ERNIE-Bot-turbo");
}

main();

```
参数传入strean为true时，返回流式结果
```ts
// 流式 测试
async function main() {
    const stream =  await client.chat({
          messages: [
              {
                  role: "user",
                  content: "等额本金和等额本息有什么区别？"
              },
          ],
          stream: true,
      }, "ERNIE-Bot-turbo");
      for await (const chunk of stream as AsyncIterableIterator<any>) {
           // process.stdout.write(chunk);
        }
}
```
### Completion 续写

对于不需要对话，仅需要根据 prompt 进行补全的场景来说，用户可以使用 `Completions` 来完成这一任务。

```ts
import {Completions} from "@baiducloud/qianfan-sdk";
// AK/SK 测试
// const client = new Completions(QIANFAN_AK, QIANFAN_SK, 'AK');
// IAM 测试
const client = new Completions(QIANFAN_ACCESS_KEY, QIANFAN_SECRET_KEY);

async function main() {
    const resp = await client.completions({
        prompt: 'Introduce the city Beijing',
    }, "SQLCoder-7B");
}

main();
```
参数传入strean为true时，返回流式结果
```ts
// 流式 
async function main() {
    const stream =  await client.completions({
        prompt: 'Introduce the city Beijing',
        stream: true,
      }, "SQLCoder-7B");
      for await (const chunk of stream as AsyncIterableIterator<any>) {
          process.stdout.write(chunk);
        }
}
main();
```

### Embedding 向量化

千帆 SDK 同样支持调用千帆大模型平台中的模型，将输入文本转化为用浮点数表示的向量形式。转化得到的语义向量可应用于文本检索、信息推荐、知识挖掘等场景。

```ts
import {Embedding} from "@baiducloud/qianfan-sdk";
// AK/SK 测试
const client = new Embedding(QIANFAN_AK, QIANFAN_SK, 'AK');
// IAM 测试
// const client = new Embedding(QIANFAN_ACCESS_KEY, QIANFAN_SECRET_KEY);
async function main() {
    const resp = await client.embedding({
        input: [ 'Introduce the city Beijing'],
    }, "Embedding-V1");
}

main();
```
