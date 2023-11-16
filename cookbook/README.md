# 千帆 Cookbook

为了帮助开发者快速上手，我们整理了大量基于千帆 SDK 使用场景的代码示例。

## Agent 相关

- [基础 Agent 构建](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/qianfan_agent/qianfan_agent.ipynb)：通过 LangChain 以及 ERNIE-Bot 的 function call 能力构建一个 Agent。
- [搜索 Agent 构建](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/function_call_agent/function_call_agent.ipynb)：利用 LangChain 实现一个具备搜索能力的 Agent。

## 千帆服务相关

- [千帆全流程示例](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/console-finetune/console-finetune.ipynb)：展示了如何使用千帆 SDK 实现数据集->SFT微调->发布模型->推理这样一个模型开发完整流程。
- [图生文示例](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/text2image/text2image.ipynb)：展示了如何使用千帆 SDK 完成图生文任务。

## 第三方组件相关

- [Baidu ElasticSearch](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/baidu_elasticsearch_RAG/qianfan_baidu_elasticsearch.ipynb)：展示了如何使用百度 ElasticSearch 向量数据库，对接千帆平台的模型管理和应用接入的能力，并构建一个RAG的知识问答场景。
- [Weights & Biases](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/wandb/wandb.ipynb)：展示了如何将千帆模型对接至 Weights & Biases，并使用其提供的可视化能力进行模型训练过程监控。 