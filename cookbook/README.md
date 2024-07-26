# 千帆 Cookbook

为了帮助开发者快速上手，我们整理了大量基于千帆 SDK 使用场景的代码示例。


# 大模型能力Cookbook
## 场景化cookbook
|        分类        | 链接                                                                                                    | 描述                                                                                                                                                                     |
|:----------------:|:------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| demo | [作文批改实操，作文批改大模型](./awesome_demo/essay_scoring/main.ipynb) | |
| | [使用千帆平台训练一个作文批改的大模型](./essay_correction.ipynb) | |
## AI原生应用相关
|        分类        | 链接                                                                                                    | 描述                                                                                                                                                                     |
|:----------------:|:------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| RAG 知识问答场景/检索式问答 | [Langchain+BES+千帆](./RAG/baidu_elasticsearch/qianfan_baidu_elasticsearch.ipynb)                       | 使用百度BES在线向量数据库                                                                                                                                                         |
|                  | [Langchain+百度向量数据VectorDB+千帆](https://cloud.baidu.com/doc/VDB/s/Nltgvlg7k)                            | 使用百度VectorDB在线向量数据库                                                                                                                                                    |
|                  | [向量数据库pinecone  + 千帆](./RAG/pinecone/pinecone_qa.ipynb)                                               | 使用pinecone在线向量数据库                                                                                                                                                      |
|                  | [向量数据库deeplake + 千帆](./RAG/deeplake_retrieval_qa.ipynb)                                               | 使用本地向量数据库                                                                                                                                                              |
|                  | [千帆 与 Weights & Biases](./wandb/wandb.ipynb)                                                          | Weights & Biases 提供了一个平台，可以对大模型的调用过程进行可视化的展现，跟踪每次请求对资源的消耗等等，尤其是在开发 Agent 等涉及到复杂的模型调用时，可以帮助开发者更好地观察模型效果并进一步去改进模型。 本文将介绍如何利用 LangChain，将千帆SDK的调用导入 Weights & Biases。     |
|                  | [知识库问答](./RAG/question_anwsering/question_answering.ipynb)                                            | 展示了如何使用 Langchian + 千帆 SDK 完成对特定文档完成获取、切分、转为向量并存储，并在之后的对话中根据所提供的文本生成回复。                                                                                                | |
|                  | [Weights & Biases](./RAG/wandb.ipynb)                                                                 | 展示了如何将千帆模型对接至 Weights & Biases，并使用其提供的可视化能力进行模型训练过程监控。                                                                                                                 | |
|      agent       | [function call langchain_agent_with_qianfan_llm](./agents/langchain_agent_with_qianfan_llm.ipynb)     | function_call，顾名思义，通过给大模型提供 function 的说明描述，以及对应的入参出参 schema，让大模型输出 function 调用策略，结合多轮对话，以最终实现一个复杂的任务。 以下将以天气获取为例子，通过千帆 Python SDK提供的 ERNIE 大模型以实现通过大模型得到对应城市的天气情况。 |
|                  | [千帆agent介绍使用 qianfan_single_action_agent_example](./agents/qianfan_single_action_agent_example.ipynb) | 以 Function Call 功能实现的千帆 Agent 模块                                                                                                                                       |
|                  | [千帆 function call 入门](./function_call.ipynb)                                                          | 以获取数据库中某类文件的数量为例子，通过调用千帆 Python SDK提供的 ERNIE 大模型以得到数据库中该语言的文件数量。                                                                                                   |
|                  | [千帆function_call工具调用](./function_call_with_tool.ipynb)                                                | 上一节千帆function_call入门展示了实现chat调用函数的功能，本节将介绍如何让chat与千帆工具进行交互，并编写更便利的调用函数。                                                                                                |
|    extensions    | [Semantic Kernel Planner](./extensions/semantic_kernel/agent_with_sk.ipynb)                           | qianfan + planner实现一个简单的demo，整体规划多步plan，在串联进行执行                                                                                                                        |
|                  | [Semantic Kernel](./extensions/semantic_kernel/chatbot_with_sk.ipynb)                                 | SK+千帆SDK以实现一个基于SK Plugin的多轮对话ChatBot.                                                                                                                                  |
|                  | [通过SK实现RAG](./extensions/semantic_kernel/rag_with_sk.ipynb)                                           | 基于SK的RAG demo                                                                                                                                                          |
|                  | [在 Llama Index 中使用千帆能力](./extensions/qianfan_with_llama_index.ipynb)                                  | LlamaIndex是一个用于连接大语言模型（LLMs）和外部数据源的数据框架。它能够让LLMs访问和利用私有或领域特定的数据，以优化模型性能并使其更加易用和流畅。本文准备了一份在 Llama Index 中使用千帆的能力进行 RAG 的示例，供用户参考。                                       |
|                  | [Sequential](./langchain_sequential.ipynb)                                                            | 本文将展示Langchain结合qianfan使用Sequential 以及 LCEL 进行大模型应用Prompt和Chain的组装调用，原文请参考Langchain Seuqential 总的来说Langchain更推荐是LCEL的方式进行实现                                            |
|        其他        | [OpenAI 适配器](./openai_adapter.ipynb)   | 对于部分已经适配 OpenAI 而尚未支持千帆 SDK 的第三库，本文提供了一种方法，可以快速将千帆适配至任意这类库。                                                                                                            |
|                   | [Prompt 优化](./apo.ipynb)：展示了如何使用 SDK 提供的 APO 功能自动地对 Prompt 进行优化，提升模型效果。|  |




# 面向管控API+SDK本地算子能力的Cookbook
## 原子能力
|        分类        | 链接                                                                                                    | 描述                                                                                                                             |
|:----------------:|:------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------|
| 数据集dataset | [如何使用千帆 Python SDK 搭配预置大模型服务进行批量推理](./dataset/batch_inference_using_dataset.ipynb) |                                                                                                                                |
| | [数据集实操](./dataset/dataset101.ipynb) |                                                                                                                                |
| | [如何在 SDK 中进行数据清洗](./dataset/how_to_use_qianfan_operator.ipynb) |                                                                                                                                |
| | [文生图数据集](./dataset/text_to_image_dataset.ipynb) |                                                                                                                                |
| 评估evaluation | [如何使用千帆 Python SDK 对模型进行评估](./evaluation/how_to_use_evaluation.ipynb) |                                                                                                                                |
| | [使用 qianfan sdk 构建本地评估模型](./evaluation/local_eval_with_qianfan.ipynb) |                                                                                                                                |
| | [在千帆 Python SDK 使用 OpenCompass 提供的评估器](./evaluation/opencompass_evaluator.ipynb) |                                                                                                                                |
| | [本地评估示例](./evaluation/auto_eval_with_qianfan.ipynb)| 使用Prompt进行渲染后，结合Dataset和本地评估器，进行自动刷库评估，并最终得到评估结果                                                                               | |
| finetune |[end-to-end的LLMops流程中的数据->SFT微调->发布->推理流程，使用的SDK版本为0.1.3。](./finetune/api_based_finetune.ipynb) |                                                                                                                                |
| | [直接使用bos进行sft并进行评估](./finetune/finetune_with_bos_and_evaluate.ipynb) |                                                                                                                                |
| | [使用文生图数据集进行模型微调](./finetune/text2image_finetune.ipynb) |                                                                                                                                |
| | [Trainer全流程使用](./finetune/trainer_finetune.ipynb) | 本例将基于qianfan SDK展示通过Dataset加载本地数据集，并上传到千帆平台，基于ERNIE-Speed-8K进行fine-tune，并使用Model进行批量跑评估数据，直到最终完成服务发布，并最终实现服务调用的完整过程。       |
| | [Trainer事件回调和可恢复性](./finetune/trainer_finetune_event_resume.ipynb) | 千帆Python SDK 在使用trainer 实现训练微调的基础上，SDK还提供了灵活的事件回调、以及trainer的可恢复的特性，以下以新建训练任务，并注册EventHandler，遇到报错之后进行resume进行演示。               |
| 推理 |[大模型推理配置自动推荐](./autotuner/tune.ipynb) | SDK 提供了推理配置自动推荐的功能，只需要提供目标场景的数据集及评估方式，设定搜索空间，SDK 就可以根据以上信息推荐出参数的配置                                                             |
| | [批量预测](./batch_prediction.ipynb) | 利用 SDK 内置的批量推理功能，在本地通过并行调用模型接口实现高效的批量预测。                                                                                       |
| | [离线批量推理](./offline_batch_inference.ipynb) | 对于时间要求不那么严格的场景，可以考虑利用平台提供的离线批量预测能力，以降低实时推理的负载压力.在进行模型评估或其他任务时，通常需要对大量数据进行预测。然而，模型推理过程往往耗时较长，通过循环串行执行会增加整体时间成本，而并行执行则需要额外的开发工作。 |
| | [千帆sdk调用一言插件](./plugin.ipynb) |                                                                                                                                |
| | [文生图示例](./text2image.ipynb)| 展示了如何使用千帆 SDK 完成文生图任务。                                                                                                         | | 
| Prompt | [Prompt使用](./prompt.ipynb) | 千帆提供了 Prompt 管理功能，可以快速地使用平台预置的优质 Prompt，或者保存用户自定义的 Prompt。SDK 也为用户快速使用 Prompt 提供了辅助。                                           |
|   | [SDXL Prompt优化](./sdxl_prompt_optimize/prompt_optimize.ipynb) | 展示了如何使用LLM进行文生图模型SDXL的Prompt优化以获得更好的图片质量和query关联度                                           |
| 其他 | [千帆 Hub](./hub.ipynb) |                                                                                                                                |
| | [ERNIE 搜索能力](./eb_search.ipynb) |                                                                                                                                |
| | [SDK 自动遗忘过长的对话历史](./auto_truncate_msg.ipynb) |                                                                                                                                |
