# 平台功能API

## API列表

百度智能云千帆平台提供了丰富的平台功能OpenAPI能力，包括TPM配额管理、私有资源池服务付费、Prompt工程、模型服务、模型管理、模型调优、数据管理、系统记忆等，详情请查看平台功能OpenAPI列表。

- TPM配额管理：提供了购买TPM配额、查询配额信息等能力。
- 私有资源池服务付费：提供了购买算力单元实例、查询算力单元实例列表或信息等能力。
- 模型服务：提供创建服务、获取服务详情等API能力。
- 模型管理：提供获取模型、模型版本详情，获取用户/预置模型及将训练任务发布为模型等API能力。
- 模型调优：提供创建训练任务、任务运行、停止任务运行及获取任务运行详情等API能力。
- 数据管理：提供创建数据集等数据集管理、导入导出数据集任务、数据清洗任务管理等API能力。
- Prompt工程：提供模板管理、Prompt优化任务、评估等API能力。
- 插件应用：提供知识库、智慧图问、天气等API能力。
- 系统记忆：提供创建系统记忆、查询系统记忆等能力。
[平台功能OpenAPI介绍](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/oly8ar9ai)

## 如何安装

```bash
npm install @baiducloud/qianfan
# or
yarn add @baiducloud/qianfan
```

## 快速使用

### 创建模型精调作业

```ts
import {consoleAction, setEnvVariable} from "@baiducloud/qianfan";

async function consoleApi() {
  const res = await consoleAction({base_api_route: '/v2/finetuning', action: 'CreateFineTuningJob', data: {"name":"test_name",
    "description":"test_description",
    "model":"ERNIE-Lite-8K-0922",
    "trainMode":"SFT"}});

    // 注意：name自定义，不可重名
    console.log(res);
}

consoleApi();
```
