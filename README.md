# 百度千帆大模型平台 SDK

[![LICENSE](https://img.shields.io/github/license/baidubce/bce-qianfan-sdk.svg)](https://github.com/baidubce/bce-qianfan-sdk/blob/master/LICENSE)
[![Release Notes](https://img.shields.io/github/release/baidubce/bce-qianfan-sdk)](https://github.com/baidubce/bce-qianfan-sdk/releases)
[![PyPI version](https://badge.fury.io/py/qianfan.svg)](https://pypi.org/project/qianfan/)
[![Documentation Status](https://readthedocs.org/projects/qianfan/badge/?version=stable)](https://qianfan.readthedocs.io/en/stable/README.html)

## 简介

![framwwork](/docs/imgs/sdk_framework.png)

千帆SDK提供大模型工具链最佳实践，让AI工作流和AI原生应用优雅且便捷地访问千帆大模型平台。SDK核心能力包含三大部分：大模型推理，大模型训练，以及通用和扩展:

- `大模型推理`：实现了对一言（ERNIE-Bot）系列、开源大模型等模型推理的接口封装，支持对话、补全、Embedding等。
- `大模型训练`：基于平台能力支持端到端的大模型训练过程，包括训练数据，精调/预训练，以及模型服务等。
- `通用与扩展`：通用能力包括了Prompt/Debug/Client等常见的AI开发工具。扩展能力则基于千帆特性适配常见的中间层框架。

## 如何安装

目前千帆Python SDK 已发布到 PyPI ，用户可使用 pip 命令进行安装，Python需要 3.7.0 或更高的版本。其他语言的SDK敬请期待。

```
pip install qianfan
```

在安装完成后，用户可以参考 [文档](./docs/cli.md) 在命令行中快速使用千帆平台功能，或者在代码内引入千帆 SDK 并使用

```python
import qianfan
```

## 快速使用

在使用千帆 SDK 之前，用户需要 [百度智能云控制台 - 安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist) 页面获取 Access Key 与 Secret Key，并在 [千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application) 中创建应用，选择需要启用的服务，具体流程参见平台 [说明文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。在获得了 Access Key 与 Secret Key 后，用户即可开始使用 SDK：

```python
import os
import qianfan

os.environ["QIANFAN_ACCESS_KEY"]="..."
os.environ["QIANFAN_SECRET_KEY"]="..."
# 通过 App Id 选择使用的应用
# 该参数可选，若不提供 SDK 会自动选择最新创建的应用
os.environ["QIANFAN_APPID"]="..."

chat_comp = qianfan.ChatCompletion(model="ERNIE-Bot")
resp = chat_comp.do(messages=[{
    "role": "user",
    "content": "你好，千帆"
}], top_p=0.8, temperature=0.9, penalty_score=1.0)

print(resp["result"])
```

除了通过环境变量设置外，千帆 SDK 还提供了 通过DotEnv加载 `.env` 文件和通过代码配置的方式，详细参见 [SDK 配置](./docs/configurable.md) 部分。

<details>
<summary> 其他认证方式 </summary>

> 这里是一些其他认证方式，请仅在无法获取 Access Key 与 Secret Key 时使用。这些认证方式已经过时，将在未来从 SDK 中移除。

API Key (**AK**) 和 Secret Key (**SK**）是用户在调用千帆模型相关功能时所需要的凭证。具体获取流程参见平台的[应用接入使用说明文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake)，但该认证方式无法使用训练、发布模型等功能，若需使用请使用 Access Key 和 Secret Key 的方式进行认证。在获得并配置了 AK 以及 SK 后，用户即可开始使用 SDK：

```python
import os
import qianfan

os.environ["QIANFAN_AK"]="..."
os.environ["QIANFAN_SK"]="..."

chat_comp = qianfan.ChatCompletion(model="ERNIE-Bot")
resp = chat_comp.do(messages=[{
    "role": "user",
    "content": "你好，千帆"
}], top_p=0.8, temperature=0.9, penalty_score=1.0)

print(resp["result"])
```

适用范围：

| 功能 | API Key | Access Key |
|:---|:---:|:---:|
| Chat 对话 | ✅ | ✅ |
| Completion 续写 | ✅ | ✅ |
| Embedding 向量化 | ✅ | ✅ |
| Plugin 插件调用 | ✅ | ✅ |
| 文生图 | ✅ | ✅ |
| 大模型调优 | ❌ | ✅ |
| 大模型管理 | ❌ | ✅ |
| 大模型服务 | ❌ | ✅ |
| 数据集管理 | ❌ | ✅ |

</details>

## 功能导览

我们提供了数个 [cookbook](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook)，可以快速了解如何使用 SDK 以及与第三方组件进行交互。

### 大模型推理

目前千帆 SDK 支持用户使用如下大模型预测能力，详见[推理服务](./docs/inference.md)

+ Chat 对话
+ Completion 续写
+ Embedding 向量化
+ Plugin 插件调用
+ Text2Image 文生图

### 大模型训练

在预置模型无法满足业务场景时，可使用大模型精调和预训练接口，来定制专属大模型。大致流程可分为：准备数据(Dataset) -> 训练(Trainer) -> 模型评估(Evaluation) -> 服务(Service)；

#### Dataset

千帆 Python SDK 集成了一系列本地的数据处理功能，允许用户在本地对来自多个数据源的数据进行增删改查等操作，详见[Dataset 框架](./docs/dataset.md)。
以下是一个通过加载本地数据集并进行数据处理的例子
```python
from qianfan.dataset import Dataset
# 从本地文件导入
ds = Dataset.load(data_file="path/to/dataset_file.jsonl")

def filter_func(row: Dict[str, Any]) -> bool:
  return "sensitive data for example" not in row["col1"]

def map_func(row: Dict[str, Any]) -> Dict[str, Any]:
  return {
    "col1": row["col1"].replace("sensitive data for example", ""),
    "col2": row["col2"]
  }

print(ds.filter(filter_func).map(map_func).list())
```

#### Trainer

千帆 Python SDK 以Pipeline为基础串联整个模型训练的流程，同时允许用户更好的把控训练流程状态 [Trainer 框架](./docs/trainer.md)。
以下是一个快速实现ERNIE-Bot-turbo fine-tuning的例子：
```python
from qianfan.dataset import Dataset
from qianfan.trainer import LLMFinetune

# 加载千帆平台上的数据集，is_download_to_local=False表示不下载数据集到本地，而是直接使用
ds: Dataset = Dataset.load(qianfan_dataset_id=111, is_download_to_local=False)

# 新建trainer LLMFinetune，最少传入train_type和dataset
# 注意fine-tune任务需要指定的数据集类型要求为有标注的非排序对话数据集。
trainer = LLMFinetune(
    train_type="ERNIE-Bot-turbo-0725",
    dataset=ds, 
)

trainer.run()

```

### 通用与扩展

#### Prompt

千帆平台支持对文生文、文生图任务的 Prompt 进行管理，详见[Prompt 管理](./docs/prompt.md)

### API Resources

平台API能力汇总，详见[**平台API能力**](./docs/api_contents.md)

### 其他
- [tokenizer](./docs/utils.md)
- [流量控制](./docs/configurable.md)

> Check [**API References**](https://qianfan.readthedocs.io/en/stable/qianfan.html) for more details.
## License

Apache-2.0
