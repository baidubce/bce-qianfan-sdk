# 百度千帆大模型平台 JavaScript SDK

针对百度智能云千帆大模型平台，我们推出了一套 JavaScript SDK（下称千帆 SDK），方便用户通过代码接入并调用千帆大模型平台的能力。

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

## 如何安装

```bash
npm install @baiducloud/qianfan
# or
yarn add @baiducloud/qianfan
```

## 快速使用

### 鉴权

在使用千帆 SDK 之前，用户需要 [百度智能云控制台 - 安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist) 页面获取 Access Key 与 Secret Key，并在 [千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application) 中创建应用，选择需要启用的服务，具体流程参见平台 [说明文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

SDK 支持从当前目录的 .env 中读取配置，也可以修改环境变量 QIANFAN_ACCESS_KEY 和 QIANFAN_SECRET_KEY ，同时支持初始化手动传入 AK/SK 。

#### env 读取

##### env 文件示例

在你项目的根目录中创建一个名为 .env 的文件，并添加以下内容：

```dotenv
QIANFAN_AK=your_access_key
QIANFAN_SK=your_secret_key
QIANFAN_ACCESS_KEY=another_access_key
QIANFAN_SECRET_KEY=another_secret_key
```

#### 修改 env 的配置

```ts
import {setEnvVariable} from "@baiducloud/qianfan";
setEnvVariable('QIANFAN_AK','***');
setEnvVariable('QIANFAN_SK','***');
 ```

#### 初始化手动传入 AK/SK

```ts
// 手动传 AK/SK 
const client = new ChatCompletion({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
// 手动传 ACCESS_KEY / SECRET_KEY
const client = new ChatCompletion({ QIANFAN_ACCESS_KEY: '***', QIANFAN_SECRET_KEY: '***' });

```

### Chat 对话

可以使用 `ChatCompletion` 对象完成对话相关操作

```ts
import {ChatCompletion} from "@baiducloud/qianfan";
// 直接读取 env
const client = new  ChatCompletion();
// 手动传 AK/SK 
// const client = new ChatCompletion({ QIANFAN_AK: '***', QIANFAN_SK: '***'});

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

参数传入 stream 为 `true` 时，返回流式结果

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
           // 返回结果
        }
}
```

### Completion 续写

对于不需要对话，仅需要根据 prompt 进行补全的场景来说，用户可以使用 `Completions` 来完成这一任务。

```ts
import {Completions} from "@baiducloud/qianfan";
// 直接读取 env  
const client = new Completions();

// 手动传 AK/SK
// const client = new Completions({ QIANFAN_AK: '***', QIANFAN_SK: '***'});

async function main() {
    const resp = await client.completions({
        prompt: 'Introduce the city Beijing',
    }, "SQLCoder-7B");
}

main();
```

参数传入 stream 为 `true` 时，返回流式结果

```ts
// 流式 
async function main() {
    const stream =  await client.completions({
        prompt: 'Introduce the city Beijing',
        stream: true,
      }, "SQLCoder-7B");
      for await (const chunk of stream as AsyncIterableIterator<any>) {
          // 返回结果
        }
}
main();
```

### Embedding 向量化

千帆 SDK 同样支持调用千帆大模型平台中的模型，将输入文本转化为用浮点数表示的向量形式。转化得到的语义向量可应用于文本检索、信息推荐、知识挖掘等场景。

```ts
import {Eembedding} from "@baiducloud/qianfan";
// 直接读取 env  
const client = new Eembedding();

// 手动传 AK/SK 测试
// const client = new Eembedding({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
async function main() {
    const resp = await client.embedding({
        input: [ 'Introduce the city Beijing'],
    }, "Embedding-V1");
}

main();
```

### 图像

#### 文生图

根据用户输入的文本生成图片。

模型支持列表
    Stable-Diffusion-XL

```ts
import * as http from 'http';
import {Text2Image} from "@baiducloud/qianfan";
// 直接读取 env  
const client = new Text2Image();

// 手动传 AK/SK 测试
// const client = new Text2Image({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
async function main() {
    const resp = await client.text2Image({
        prompt: '生成爱莎公主的图片',
        size: '768x768',
        n: 1,
        steps: 20,
        sampler_index: 'Euler a',
    }, 'Stable-Diffusion-XL');

    const base64Image = resp.data[0].b64_image;
    // 注意 base64Image没有带ata:image/jpeg;base64 前缀，要直接使用的话，需要加上
    // 创建一个简单的服务器
    const server = http.createServer((req, res) => {
        res.writeHead(200, {'Content-Type': 'text/html'});
        let html = `<html><body><img src="data:image/jpeg;base64,${base64Image}" /><br/></body></html>`;
        res.end(html);
    });
    const port = 3001;
    server.listen(port, () => {
        console.log(`服务器运行在 http://localhost:${port}`);
    });
}

main();
```

#### 图生文

多模态图像理解模型，可以支持多样的图像分辨率，回答图形图表有关问题
注意事项：调用本文API，推荐使用安全认证AK/SK鉴权，调用流程及鉴权介绍详见SDK安装及使用流程

```ts
import {Image2Text} from "@baiducloud/qianfan";
// 直接读取 env  
const client = new Image2Text({Endpoint: '***'});

// 手动传 AK/SK 测试
// const client = new Image2Text({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
async function main() {
    const resp = await client.image2Text({
        prompt: '分析一下图片画了什么',
        image: '图片的base64编码',
    });
}

main();

```

```ts
import {Image2Text} from "@baiducloud/qianfan";
// 直接读取 env 
// 使用预置服务Fuyu-8B
const client = new Image2Text();

// 手动传 AK/SK 测试
// const client = new Image2Text({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
async function main() {
    const resp = await client.image2Text({
        prompt: '分析一下图片画了什么',
        image: '图片的base64编码',
    });
}

main();

```

### Plugin 插件

SDK支持使用平台插件能力，以帮助用户快速构建 LLM 应用或将 LLM 应用到自建程序中。支持知识库、智慧图问、天气等插件。

#### 千帆插件

```ts
// 天气插件
async function main() {
    const resp = await client.plugins({
        query: '深圳今天天气如何',
        /** 
         *  插件名称
         * 知识库插件固定值为["uuid-zhishiku"] 
         * 智慧图问插件固定值为["uuid-chatocr"]
         * 天气插件固定值为["uuid-weatherforecast"]
         */ 
        plugins: [
            'uuid-weatherforecast',
        ],
    });
}

// 智慧图问
async function chatocrMain() {
    const resp = await client.plugins({
        query: '请解析这张图片, 告诉我怎么画这张图的简笔画',
        plugins: [
            'uuid-chatocr',
        ],
        fileurl: 'https://xxx.bcebos.com/xxx/xxx.jpeg',
    });
}

// 知识库
async function zhishikuMain() {
    const reps = await client.plugins({
        query: '你好什么时候飞行员需要负法律责任？',
        plugins: [
            'uuid-zhishiku',
        ],
    });
}

main();

// chatocrMain();

// zhishikuMain();
```

参数传入 stream 为 `true` 时，返回流式结果

```ts
import {Plugin} from "@baiducloud/qianfan";
// 直接读取 env  
const client = new Plugin();

// 手动传 AK/SK 测试
// const client = new Plugins({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
async function main() {
    const stream = await client.plugins({
        query: '深圳今天天气如何',
        /** 
         *  插件名称
         * 知识库插件固定值为["uuid-zhishiku"] 
         * 智慧图问插件固定值为["uuid-chatocr"]
         * 天气插件固定值为["uuid-weatherforecast"]
         */ 
        plugins: [
            'uuid-weatherforecast',
        ],
        stream: true,
    });
    for await (const chunk of stream as AsyncIterableIterator<any>) {
        // 返回结果
    }
}

main();
```

#### 一言插件 API-V2

* 说图解画（ImageAI）：基于图片进行文字创作、回答问题，帮你写文案、想故事、图生图。暂仅支持10MB以内的图片。
* 览卷文档（ChatFile）：原ChatFile，可基于文档完成摘要、问答、创作等任务，仅支持10MB以内文档，不支持扫描件。
* E言易图（eChart）：基于Apache Echarts为您提供数据洞察和图表制作，目前支持柱状图、折线图、饼图、雷达图、散点图、漏斗图、思维导图（树图）。

eChart插件

```ts
// eChart插件
async function yiYaneChartMain() {
    const resp = await client.plugins({
        messages: [
            {
                "role": "user",
                "content": "帮我画一个饼状图：8月的用户反馈中，BUG有100条，需求有100条，使用咨询100条，总共300条反馈"
            }
        ],
        plugins: ["eChart"],
    });
}

yiYaneChartMain() 

// ImageAI插件测试
async function yiYanImageAIMain() {
    const resp = await client.plugins({
        messages: [
            {
                "role": "user",
                "content": "<img>cow.jpeg</img><url>https://xxx/xxx/xxx.jpeg</url> 这张图片当中都有啥"
            }
        ],
        plugins: ["ImageAI"],
    });
}

yiYanImageAIMain()

// ChatFile测试
async function yiYanChatFileMain() {
    const resp = await client.plugins({
        messages: [
            {'role': 'user', 'content': '<file>浅谈牛奶的营养与消费趋势.docx</file><url>https://xxx/xxx/xxx.docx</url>'},
            // eslint-disable-next-line max-len
            {'role': 'assistant', 'content': '以下是该文档的关键内容：\n牛奶作为一种营养丰富、易消化吸收的天然食品，受到广泛欢迎。其价值主要表现在营养成分和医学价值两个方面。在营养成分方面，牛奶含有多种必需的营养成分，如脂肪、蛋白质、乳糖、矿物质和水分等，比例适中，易于消化吸收。在医学价值方面，牛奶具有促进生长发育、维持健康水平的作用，对于儿童长高也有积极影响。此外，牛奶还具有极高的市场前景，消费者关注度持续上升，消费心理和市场需求也在不断变化。为了更好地发挥牛奶的营养价值，我们应该注意健康饮用牛奶的方式，适量饮用，并根据自身情况选择合适的牛奶产品。综上所述，牛奶作为一种理想的天然食品，不仅具有丰富的营养成分，还具有极高的医学价值和市场前景。我们应该充分认识牛奶的价值，科学饮用，让牛奶为我们的健康发挥更大的作用。'},
            {'role': 'user', 'content': '牛奶的营养成本有哪些'},
        ],
        plugins: ['ChatFile']
    });
}
yiYanChatFileMain();
```
