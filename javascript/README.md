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

浏览器环境使用请参考 [文档](https://github.com/baidubce/bce-qianfan-sdk/blob/main/docs/javascript/browser.md)

## 快速使用

## 第一步：安装node.js sdk

```bash
#如果使用npm：
npm install @baiducloud/qianfan
#如果使用yarn：
yarn add @baiducloud/qianfan
```

## 第二步：获得鉴权

在使用千帆 SDK 之前，用户需要 [百度智能云控制台 - 安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist) 页面获取 Access Key 与 Secret Key，并在 [千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application) 中创建应用，选择需要启用的服务，具体流程参见平台 [说明文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

### 选择一：使用安全认证AK/SK鉴权   【推荐】

（1）登录百度智能云千帆控制台，点击“用户账号->安全认证”进入Access Key管理界面。

（2）查看安全认证页面的Access Key/Secret Key

注意：
初始化鉴权时，使用“安全认证/Access Key”中的Access Key和 Secret Key进行鉴权，更多鉴权认证机制请参考鉴权认证机制。
安全认证Access Key(AK)/Secret Key(SK)，和使用的获取AcessToken的应用API Key(AK) 和 Secret Key(SK)不同

### 选择二：使用应用AK/SK鉴权调用 【不推荐，后续可能出现新功能不兼容的情况】

（1）登录百度智能云千帆控制台。
   注意：为保障服务稳定运行，账户最好不处于欠费状态。

（2）创建千帆应用。
如果已有应用，此步骤可跳过。如果无应用，进入控制台创建应用 ，如何创建应用也可以参考应用接入使用。

（3）在应用接入页，获取应用的API Key、Secret Key。

## 第三步：初始化AK和SK

### 选择一：通过配置文件初始化 【推荐】

在项目的根目录中创建一个名为 .env 的文件，并添加以下内容，SDK从当前目录的 .env 中读取配置。

```bash
QIANFAN_AK=your_access_key
QIANFAN_SK=your_secret_key
QIANFAN_ACCESS_KEY=another_access_key
QIANFAN_SECRET_KEY=another_secret_key
```

### 选择二：通过环境变量初始化

```bash
setEnvVariable('QIANFAN_AK','your_api_key');
setEnvVariable('QIANFAN_SK','your_secret_key');
```

### 选择三：通过参数初始化（以ChatCompletion为例）

```js
import {ChatCompletion} from "@baiducloud/qianfan";

// 通过参数初始化，应用API Key替换your_api_key，应用Secret Key替换your_secret_key，以对话Chat为例，调用如下
const client = new ChatCompletion({ QIANFAN_AK: 'your_api_key', QIANFAN_SK: 'your_secret_key' });
// 通过参数初始化， ACCESS_KEY / SECRET_KEY
const client = new ChatCompletion({ QIANFAN_ACCESS_KEY: 'your_api_key', QIANFAN_SECRET_KEY: 'your_secret_key' });
```

## 第四步：使用SDK

> 我们提供了一些 [示例](./examples)，可以帮助快速了解 SDK 的使用方法并完成常见功能。
功能如下：

### Chat 单轮对话

#### 默认模型

```ts
import {ChatCompletion, setEnvVariable} from "@baiducloud/qianfan";

setEnvVariable('QIANFAN_ACCESS_KEY','***');
setEnvVariable('QIANFAN_SECRET_KEY','***');

const client = new  ChatCompletion();
async function main() {
    const resp = await client.chat({
        messages: [
            {
                role: 'user',
                content: '你好！',
            },
        ],
    });
    console.log(resp);
}

main();
```

```bash
{
  id: 'as-xdiknr8pj9',
  object: 'chat.completion',
  created: 1709721393,
  result: '你好！有什么我可以帮助你的吗？',
  is_truncated: false,
  need_clear_history: false,
  usage: { prompt_tokens: 2, completion_tokens: 8, total_tokens: 10 }
}
```

#### 指定预置模型

```ts
import {ChatCompletion, setEnvVariable} from "@baiducloud/qianfan";

const client = new  ChatCompletion();
async function main() {
    const resp = await client.chat({
        messages: [
            {
                role: 'user',
                content: '今天深圳天气',
            },
        ],
     }, "ERNIE-Lite-8K");
    console.log(resp);
}

main();
```

#### 用户自行发布的模型服务  

```ts
import {ChatCompletion, setEnvVariable} from "@baiducloud/qianfan";

const client = new  ChatCompletion({Endpoint: '***'});
async function main() {
    const resp = await client.chat({
        messages: [
            {
                role: 'user',
                content: '你好！',
            },
        ],
    });
    console.log(resp);
}

main
```

### 多轮对话

```ts
import {ChatCompletion, setEnvVariable} from "@baiducloud/qianfan";

const client = new  ChatCompletion();  
async function main() {    // 调用默认模型，即 ERNIE--turbo
    const resp = await client.chat({
        messages: [
            {
                role: 'user',
                content: '你好！',
            },
            {
                 role: "assistant",
                 content: "你好，请问有什么我可以帮助你的吗？"
             },
             {
                 role: "user",
                 "content": "我在北京，周末可以去哪里玩？"
             },
        ],
    });
    console.log(resp);
}

main();
```

```bash
{
  id: 'as-8vcq0n4u0e',
  object: 'chat.completion',
  created: 1709887877,
  result: '北京是一个拥有许多有趣和独特景点的大城市，周末你可以去很多地方玩。例如：
' +
    '
' +
    '1. **故宫博物院**：这是中国最大的古代建筑群，有着丰富的历史和文化遗产，是个很好的适合全家人游玩的地方。
' +
    '2. **天安门广场**：这里是北京的心脏，周围有许多历史和现代建筑。你可以在广场上漫步，欣赏升旗仪式和观看周围的繁华景象。
' +
    '3. **颐和园**：这是一个美丽的皇家园林，有着优美的湖泊和精美的古建筑。你可以在这里漫步，欣赏美丽的景色，同时也可以了解中国的传统文化。
' +
    '4. **北京动物园**：这是中国最大的动物园之一，有许多稀有动物，包括熊猫、老虎、长颈鹿等。对于孩子们来说是个很好的去处。
' +
    '5. **798艺术区**：这是一个充满艺术气息的地方，有许多画廊、艺术工作室和艺术展览。这里有许多新的现代艺术作品，可以欣赏到一些艺术家的创作。
' +
    '6. **三里屯酒吧街**：如果你对夜生活感兴趣，可以去三里屯酒吧街。这里有许多酒吧和餐馆，是一个热闹的夜生活场所。
' +
    '7. **北京环球度假区**：如果你们喜欢主题公园，那么可以去环球度假区，虽然这是在建的，但是等它建好之后肯定是一个很好的去处。
' +
    '
' +
    '当然，你也可以考虑一些其他的地方，比如购物街、博物馆、公园等等。希望这些建议对你有所帮助！',
  is_truncated: false,
  need_clear_history: false,
  usage: { prompt_tokens: 19, completion_tokens: 307, total_tokens: 326 }
}
```

### 流式输出

通过传入 stream: true

```ts
import {ChatCompletion, setEnvVariable} from "@baiducloud/qianfan";

const client = new  ChatCompletion();
async function main() {
    const stream = await client.chat({
        messages: [
            {
                role: 'user',
                content: '你好！',
            },
        ],
        stream: true,   //启用流式返回
    });
      for await (const chunk of stream as AsyncIterableIterator<any>) {
        console.log(chunk);
    }
}

main();
```

```bash
{
  id: 'as-f7mrqpanb3',
  object: 'chat.completion',
  created: 1709724132,
  sentence_id: 0,
  is_end: false,
  is_truncated: false,
  result: '你好！',
  need_clear_history: false,
  usage: { prompt_tokens: 2, completion_tokens: 0, total_tokens: 2 }
}
{
  id: 'as-f7mrqpanb3',
  object: 'chat.completion',
  created: 1709724132,
  sentence_id: 1,
  is_end: false,
  is_truncated: false,
  result: '有什么我可以帮助你的吗？',
  need_clear_history: false,
  usage: { prompt_tokens: 2, completion_tokens: 0, total_tokens: 2 }
}
{
  id: 'as-f7mrqpanb3',
  object: 'chat.completion',
  created: 1709724132,
  sentence_id: 2,
  is_end: true,
  is_truncated: false,
  result: '',
  need_clear_history: false,
  usage: { prompt_tokens: 2, completion_tokens: 8, total_tokens: 10 }
}
```

### 续写Completions

千帆 SDK 支持调用续写Completions相关API，支持非流式、流式调用。

#### 默认模型

```ts
import {Completions, setEnvVariable} from "@baiducloud/qianfan";

const client = new Completions({ QIANFAN_ACCESS_KEY: 'your_iam_ak', QIANFAN_SECRET_KEY: 'your_iam_sk' });
async function main() {
    const resp = await client.completions({
        prompt: 'In Bash, how do I list all text files in the current directory (excluding subdirectories) that have been modified in the last month',
    });
    console.log(resp);
}

main();
```

#### 指定预置模型

```ts
import {Completions, setEnvVariable} from "@baiducloud/qianfan";

const client = new Completions();
async function main() {
    const resp = await client.completions({
        prompt: '你好',
    }, 'ERNIE-3.5-8K');
    console.log(resp);
}

main();
```

#### 用户自行发布的模型服务  

通过Endpoint传入服务地址

```ts
import {Completions, setEnvVariable} from "@baiducloud/qianfan";

const client = new Completions({QIANFAN_ACCESS_KEY: '***', QIANFAN_SECRET_KEY: '***', Endpoint: '***'});
async function main() {
    const resp = await client.completions({
        prompt: '你好，你是谁',
    });
    console.log(resp);
}

main();
```

```bash
{
  id: 'as-hfmv5mvdim',
  object: 'chat.completion',
  created: 1709779789,
  result: '你好！请问有什么我可以帮助你的吗？无论你有什么问题或需要帮助，我都会尽力回答和提供支持。请随时告诉我你的需求，我会尽快回复你。',
  is_truncated: false,
  need_clear_history: false,
  finish_reason: 'normal',
  usage: { prompt_tokens: 1, completion_tokens: 34, total_tokens: 35 }
}
```

#### 流式调用

通过传入 stream: true

```ts
import {Completions, setEnvVariable} from "@baiducloud/qianfan";

const client = new Completions({ QIANFAN_ACCESS_KEY: '***', QIANFAN_SECRET_KEY: '***' });
async function main() {
    const stream = await client.completions({
        prompt: '你好，你是谁',
        stream: true,   //启用流式返回
    });
     for await (const chunk of stream as AsyncIterableIterator<any>) {
        console.log(chunk);
    }
}

main();
```

```bash
{
  id: 'as-cck51r1rfw',
  object: 'chat.completion',
  created: 1709779938,
  sentence_id: 0,
  is_end: false,
  is_truncated: false,
  result: '你好！',
  need_clear_history: false,
  finish_reason: 'normal',
  usage: { prompt_tokens: 1, completion_tokens: 2, total_tokens: 3 }
}
{
  id: 'as-cck51r1rfw',
  object: 'chat.completion',
  created: 1709779938,
  sentence_id: 1,
  is_end: false,
  is_truncated: false,
  result: '请问有什么可以帮助你的吗？',
  need_clear_history: false,
  finish_reason: 'normal',
  usage: { prompt_tokens: 1, completion_tokens: 2, total_tokens: 3 }
}
{
  id: 'as-cck51r1rfw',
  object: 'chat.completion',
  created: 1709779938,
  sentence_id: 2,
  is_end: true,
  is_truncated: false,
  result: '',
  need_clear_history: false,
  finish_reason: 'normal',
  usage: { prompt_tokens: 1, completion_tokens: 8, total_tokens: 9 }
}
```

### 向量Embeddings

千帆 SDK 同样支持调用千帆大模型平台中的模型，将输入文本转化为用浮点数表示的向量形式。转化得到的语义向量可应用于文本检索、信息推荐、知识挖掘等场景。

#### 默认模型

```ts
import {Embedding} from "@baiducloud/qianfan";

const client = new Embedding();
async function main() {
    const resp = await client.embedding({
        input: ['介绍下你自己吧', '你有什么爱好吗？'],
    });
    const data = resp.data[0] as any;
    console.log(data.embedding);
}

main();
```

```bash
[0.06814255565404892,  0.007878394797444344,  0.060368239879608154, ...]
[0.13463851809501648,  -0.010635783895850182,   0.024348173290491104, ...]
```

#### 指定模型

Embedding-V1

```ts

import {Eembedding} from "@baiducloud/qianfan";

const client = new Eembedding({ QIANFAN_ACCESS_KEY: '***', QIANFAN_SECRET_KEY: '***' });
async function main() {
    const resp = await client.embedding({
        input: ['介绍下你自己吧', '你有什么爱好吗？'],
    }, 'Embedding-V1');
    const data = resp.data[0] as any;
    console.log(data.embedding);
}

main();
```

```bash
[0.13463850319385529,  -0.010635782964527607,   0.024348171427845955...]
```

### 图像-Images

#### 文生图

```ts
import * as http from 'http';
import {Text2Image, setEnvVariable} from "@baiducloud/qianfan";
const client = new Text2Image({Endpoint：'***'});

async function main() {
    const resp = await client.text2Image({
        prompt: 'A Ragdoll cat with a bowtie.',
    });

    const base64Image = resp.data[0].b64_image;
    // 创建一个简单的服务器
    const server = http.createServer((req, res) => {
        res.writeHead(200, {'Content-Type': 'text/html'});
        let html = `<html><body><img src="data:image/jpeg;base64,${base64Image}" /><br/></body></html>`;
        res.end(html);
    });

    const port = 3002;
    server.listen(port, () => {
        console.log(`服务器运行在 http://localhost:${port}`);
    });
}

main();
```

#### 图生文

##### 预置模型Fuyu-8B

```ts
import {setEnvVariable} from '@baiducloud/qianfan'
import {Image2Text} from "@baiducloud/qianfan";

// 调用大模型
const client = new Image2Text();
async function main() {
    const resp = await client.image2Text({
        prompt: '分析一下图片画了什么',
        image: 'iVBORw0KGgoAAAANSUhEUgAAB4IAAxxxxxxxxxxxx=',  //  请替换图片的base64编码
    });
    console.log(resp.result)
}

main();
```

##### 用户自定义模型

```ts
import {setEnvVariable} from '@baiducloud/qianfan'
import {Image2Text} from "@baiducloud/qianfan";

// 调用大模型
const client = new Image2Text({Endpoint: '***'});
async function main() {
    const resp = await client.image2Text({
        prompt: '分析一下图片画了什么',
        image: 'iVBORw0KGgoAAAANSUhEUgAAB4IAAxxxxxxxxxxxx=',  //  请替换图片的base64编码
    });
    console.log(resp.result)
}

main();
```

### Plugin 插件

#### 千帆插件

SDK支持使用平台插件能力，以帮助用户快速构建 LLM 应用或将 LLM 应用到自建程序中。支持知识库、智慧图问、天气等插件。

```ts
import {Plugin} from "@baiducloud/qianfan";
// 注意：千帆插件需要传入Endpoint， 一言插件不用
const client = new Plugin({Endpoint: '***'});

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

#### 一言插件 API-V2

说图解画（ImageAI）：基于图片进行文字创作、回答问题，帮你写文案、想故事、图生图。暂仅支持10MB以内的图片。
览卷文档（ChatFile）：原ChatFile，可基于文档完成摘要、问答、创作等任务，仅支持10MB以内文档，不支持扫描件。
E言易图（eChart）：基于Apache Echarts为您提供数据洞察和图表制作，目前支持柱状图、折线图、饼图、雷达图、散点图、漏斗图、思维导图（树图）。

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

### Reranker 重排序

跨语种语义表征算法模型，擅长优化语义搜索结果和语义相关顺序精排，支持中英日韩四门语言。

```ts
import {Reranker} from "@baiducloud/qianfan";
// 直接读取 env  
const client = new Reranker();

async function main() {
     const resp = await client.reranker({
        query: '上海天气',
        documents: ['上海气候', '北京美食'],
    });
}

main();

```

## 通过其他集成了sdk的库来使用

### langchain
#### 安装langchain库
```npm install @langchain/baidu-qianfan```

#### 添加环境变量(或作为函数参数传入)

```bash
export QIANFAN_AK=""
export QIANFAN_SK=""
export QIANFAN_ACCESS_KEY=""
export QIANFAN_SECRET_KEY=""
```

#### 示例

```ts

import { ChatBaiduQianfan } from "@langchain/baidu-qianfan";
import { HumanMessage } from "@langchain/core/messages";

const chat = new ChatBaiduQianfan({
    model: 'ERNIE-Lite-8K'
});
const message = new HumanMessage("北京天气");

const res = await chat.invoke([message]);

```

```ts

import { BaiduQianfanEmbeddings } from "@langchain/baidu-qianfan";

const embeddings = new BaiduQianfanEmbeddings();
const res = await embeddings.embedQuery("Introduce the city Beijing");

```