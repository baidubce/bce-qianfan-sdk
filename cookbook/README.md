# 千帆 Cookbook

为了帮助开发者快速上手，我们整理了大量基于千帆 SDK 使用场景的代码示例。

## 千帆服务相关

- [千帆全流程示例](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/finetune/console-finetune.ipynb)：展示了如何使用千帆 SDK 实现数据集->SFT微调->发布模型->推理这样一个模型开发完整流程。
- [图生文示例](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/text2image.ipynb)：展示了如何使用千帆 SDK 完成图生文任务。
- [ERNIE Bot 搜索能力示例](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/eb_search.ipynb)：展示了 ENRIE Bot 的搜索增强能力和使用方法。
- [批量预测示例](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/eb_search.ipynb)：展示了如何使用 SDK 批量对数据进行预测。
- [Prompt 模版](./prompt.ipynb)：展示了如何使用 SDK 管理和使用 Prompt。


## Agent 相关

- [Langchain Qianfan Agent](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/agents/langchain_agent_with_qianfan_llm.ipynb)：通过 LangChain 以及 ERNIE-Bot 的 function call 结合，构建一个实时查询天气的 Agent。
- [Function call](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/agents/qianfan_single_action_agent_example.ipynb)：利用千帆库Extension中的 QianfanSingleActionAgent , 实现一个论文检索并获取作者信息的 Agent。

## RAG相关

- [知识库问答](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/RAG/question_anwsering/question_answering.ipynb)：展示了如何使用 Langchian + 千帆 SDK 完成对特定文档完成获取、切分、转为向量并存储，并在之后的对话中根据所提供的文本生成回复。
- [Baidu ElasticSearch](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/RAG/baidu_elasticsearch/qianfan_baidu_elasticsearch.ipynb)：展示了如何使用百度 ElasticSearch 向量数据库，对接千帆平台的模型管理和应用接入的能力，并构建一个RAG的知识问答场景。
- [Weights & Biases](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/RAG/wandb.ipynb)：展示了如何将千帆模型对接至 Weights & Biases，并使用其提供的可视化能力进行模型训练过程监控。 
- [Deep Lake](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/RAG/deeplake_retrieval_qa.ipynb)：展示了如何使用 Deep Lake 获取数据库，并基于该数据完成一个检索式问答系统。
