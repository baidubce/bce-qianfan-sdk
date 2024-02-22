# 百度千帆大模型平台 JavaScript SDK

[![license][license-image]][license-url]
[![codecov][codecov-image]][codecov-url]
[![NPM version][npm-image]][npm-url]
[![NPM downloads][download-image]][download-url]
[![docs][docs-image]][docs-url]
[![Feedback Issue][issue-image]][issue-url]
[![Feedback Ticket][ticket-image]][ticket-url]

[license-image]: https://img.shields.io/github/license/baidubce/bce-qianfan-sdk.svg
[license-url]: https://github.com/baidubce/bce-qianfan-sdk/blob/main/LICENSE
[codecov-image]: https://img.shields.io/codecov/c/github/baidubce/bce-qianfan-sdk/main
[codecov-url]: https://codecov.io/gh/baidubce/bce-qianfan-sdk/branch/main
[npm-image]: http://img.shields.io/npm/v/@baiducloud/qianfan
[npm-url]: http://npmjs.org/package/@baiducloud/qianfan
[download-image]: https://img.shields.io/npm/dm/@baiducloud/qianfan
[download-url]: https://npmjs.org/package/@baiducloud/qianfan
[docs-image]: https://img.shields.io/badge/docs-qianfan%20sdk-blue?style=flat-square
[docs-url]: https://github.com/baidubce/bce-qianfan-sdk/blob/main/javascript/README.md
[issue-image]: https://img.shields.io/badge/%E8%81%94%E7%B3%BB%E6%88%91%E4%BB%AC-GitHub_Issue-brightgreen
[issue-url]: https://github.com/baidubce/bce-qianfan-sdk/issues
[ticket-image]: https://img.shields.io/badge/%E8%81%94%E7%B3%BB%E6%88%91%E4%BB%AC-%E7%99%BE%E5%BA%A6%E6%99%BA%E8%83%BD%E4%BA%91%E5%B7%A5%E5%8D%95-brightgreen
[ticket-url]: https://console.bce.baidu.com/ticket/#/ticket/create?productId=279

针对百度智能云千帆大模型平台，我们推出了一套 JavaScript SDK（下称千帆 SDK），方便用户通过代码接入并调用千帆大模型平台的能力。

## 如何安装

```bash
npm install @baiducloud/qianfan
# or
yarn add @baiducloud/qianfan
```

## 快速使用

### 鉴权

在使用千帆 SDK 之前，用户需要 [百度智能云控制台 - 安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist) 页面获取 Access Key 与 Secret Key，并在 [千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application) 中创建应用，选择需要启用的服务，具体流程参见平台 [说明文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

env 读取

```ts
const QIANFAN_AK = process.env.QIANFAN_AK || '';
const QIANFAN_SK = process.env.QIANFAN_SK || '';
const QIANFAN_ACCESS_KEY = process.env.QIANFAN_ACESS_KEY || '';
const QIANFAN_SECRET_KEY = process.env.QIANFAN_SECRET_KEY || '';
```

默认 IAM 认证方式，如果使用 AK/SK 方式鉴权，需要传入 Type 参数, 参数值如下：'AK'  

```ts
// AK/SK    
 const client = new  ChatCompletion(QIANFAN_AK, QIANFAN_SK, 'AK');
// IAM 
const client = new ChatCompletion(QIANFAN_ACCESS_KEY, QIANFAN_SECRET_KEY);

// TO DO！！！
// 下期优化支持 env 和手动传入
```

### Chat 对话

可以使用 `ChatCompletion` 对象完成对话相关操作

```ts
import {ChatCompletion} from "@baiducloud/qianfan";
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

参数传入 strean 为 true 时，返回流式结果

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
import {Completions} from "@baiducloud/qianfan";
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

参数传入 strean 为 true 时，返回流式结果

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
import {Embedding} from "@baiducloud/qianfan";
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
