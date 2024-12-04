# 安装千帆 Python SDK

目前，千帆 Python SDK 提供了多种可选的安装选项，用于保证依赖最小的情况下能够满足用户的多种需求。

所有安装选项都可以通过在安装时使用 `[]` 来指定，例如：`pip install "qianfan[dataset_base]"` 

现在的 SDK 中提供了如下安装选项使用：

+ 无安装选项（默认情况）：仅支持 API 调用的轻量场景，包括推理、发起在线训练等，可以使用 CLI
+ `dataset_base`: 额外安装用于离线批量推理和本地数据处理的依赖组件
+ `openai`: 额外安装用于启动 OpenAI Adapter Server 的依赖，用于把 OpenAI 的请求转换为指向千帆平台的请求
+ `langchain`: 在 `dataset_base` 的基础上，额外安装 langchain。可以使用千帆 Python SDK 提供的 Agent 组件。
+ `local_data_clean`: 在 `dataset_base` 的基础上，额外安装本地数据清洗算子所使用的依赖组件
+ `all`: 安装上述所有的依赖

用户可以根据自己的需要来指定安装的依赖选项
