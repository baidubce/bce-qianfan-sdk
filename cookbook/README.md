# 千帆 Cookbook

为了帮助开发者快速上手，我们整理了大量基于千帆 SDK 使用场景的代码示例。

# 大模型推理


- [文生图示例](./text2image.ipynb)：展示了如何使用千帆 SDK 完成文生图任务。
- [ERNIE Bot 搜索能力示例](./eb_search.ipynb)：展示了 ENRIE Bot 的搜索增强能力和使用方法。
- [批量推理示例](./batch_prediction.ipynb)：展示了如何使用 SDK 批量对数据进行预测。
- [离线批量推理](./offline_batch_inference.ipynb)：展示了如何使用 SDK 调用平台的离线批量功能。

## 推理配置推荐

- [基本使用](./autotuner/tune.ipynb)：展示了如何使用千帆 SDK 所提供的大模型推理配置推荐功能，去寻找更适合目标场景的配置以提高模型性能。


# 大模型训练

## Dataset

- [简易数据集操作样例](./dataset/dataset101.ipynb)：展示了如何使用千帆 SDK 集成的数据集功能进行数据处理
- [如何使用 SDK 发起在线数据清洗](./dataset/how_to_use_qianfan_operator.ipynb)：展示了如何使用千帆 SDK 发起在线数据清洗任务
- [使用数据集进行批量推理](./dataset/batch_inference_using_dataset.ipynb)：展示了数据集与千帆模型和服务结合的批量推理能力

## Trainer

- [Finetune精调示例](./finetune/trainer_finetune.ipynb)：展示了如何使用千帆SDK `Trainer` 实现数据集->SFT微调->发布模型->模型评估->服务部署->推理这样一个模型开发完整流程。
- [Finetune事件控制](./finetune/trainer_finetune_event_resume.ipynb)：展示了如何使用千帆SDK `Trainer` 实现事件回调，任务恢复等功能

## Evaluation

- [评估示例](./evaluation/how_to_use_evaluation.ipynb) 支持发起平台和本地两种评估任务，并且在本地获取评估报告
- [本地评估示例](./evaluation/auto_eval_with_qianfan.ipynb)：使用Prompt进行渲染后，结合Dataset和本地评估器，进行自动刷库评估，并最终得到评估结果

# AI 原生应用相关

- [Prompt 模版](./prompt.ipynb)：展示了如何使用 SDK 管理和使用 Prompt。
- [OpenAI 适配器](./openai_adapter.ipynb)：展示了如何使用 SDK 提供的 OpenAI 适配器快速接入已经支持 OpenAI 接口的第三方库。

## Agent

- [Langchain Qianfan Agent](./agents/langchain_agent_with_qianfan_llm.ipynb)：通过 LangChain 以及 ERNIE-Bot 的 function call 结合，构建一个实时查询天气的 Agent。
- [Function call](./agents/qianfan_single_action_agent_example.ipynb)：利用千帆库Extension中的 QianfanSingleActionAgent , 实现一个论文检索并获取作者信息的 Agent。

## RAG

- [知识库问答](./RAG/question_anwsering/question_answering.ipynb)：展示了如何使用 Langchian + 千帆 SDK 完成对特定文档完成获取、切分、转为向量并存储，并在之后的对话中根据所提供的文本生成回复。
- [Baidu ElasticSearch](./RAG/baidu_elasticsearch/qianfan_baidu_elasticsearch.ipynb)：展示了如何使用百度 ElasticSearch 向量数据库，对接千帆平台的模型管理和应用接入的能力，并构建一个RAG的知识问答场景。
- [Weights & Biases](./RAG/wandb.ipynb)：展示了如何将千帆模型对接至 Weights & Biases，并使用其提供的可视化能力进行模型训练过程监控。 
- [Deep Lake](./RAG/deeplake_retrieval_qa.ipynb)：展示了如何使用 Deep Lake 获取数据库，并基于该数据完成一个检索式问答系统。
- [Pinecone](./RAG/pinecone/pinecone_qa.ipynb)：展示了如何使用 Pinecone 获取数据库，并基于该数据完成一个检索式问答系统。


# 其他

- [精调接口示例](./finetune/api_based_finetune.ipynb)：展示了如何使用千帆 SDK 实现数据集->SFT微调->发布模型->推理这样一个模型开发完整流程。
