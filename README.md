# 百度千帆大模型平台 SDK

[![LICENSE](https://img.shields.io/github/license/baidubce/bce-qianfan-sdk.svg)](https://github.com/baidubce/bce-qianfan-sdk/blob/master/LICENSE)
[![Release Notes](https://img.shields.io/github/release/baidubce/bce-qianfan-sdk)](https://github.com/baidubce/bce-qianfan-sdk/releases)
[![PyPI version](https://badge.fury.io/py/qianfan.svg)](https://pypi.org/project/qianfan/)
[![Documentation Status](https://readthedocs.org/projects/qianfan/badge/?version=stable)](https://qianfan.readthedocs.io/en/stable/README.html)

针对百度智能云千帆大模型平台，我们推出了一套 Python SDK（下称千帆 SDK），方便用户通过代码接入并调用千帆大模型平台的能力。

## 如何安装

目前千帆 SDK 已发布到 PyPI ，用户可使用 pip 命令进行安装。安装千帆 SDK 需要 3.7.0 或更高的 Python 版本

```
pip install qianfan
```

在安装完成后，用户即可在代码内引入千帆 SDK 并使用

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

除了通过环境变量设置外，千帆 SDK 还提供了 `.env` 文件和通过代码配置的方式，详细参见 [SDK 配置](./docs/configurable.md) 部分。

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

### 大模型能力

目前千帆 SDK 支持用户使用如下大模型预测能力，详见[预测服务](./docs/inference.md)

+ Chat 对话
+ Completion 续写
+ Embedding 向量化
+ Plugin 插件调用
+ 文生图

### 大模型调优

目前千帆平台支持如下训练调优能力，详见[训练调优](./docs/train.md)
- 创建训练任务
- 创建任务运行
- 获取任务运行详情
- 停止任务运行

### 模型管理

目前千帆平台支持对训练完成后的模型进行管理，详见[模型管理](./docs/model_management.md)

- 获取模型详情
- 获取模型版本详情
- 训练任务发布为模型

### 模型服务

千帆平台支持将模型发布成服务，详见[服务管理](./docs/service.md)

- 创建服务
- 查询服务详情

### 数据集管理

千帆平台提供 API 接口对数据集进行管理，详见[数据管理](./docs/dataset.md)

目前支持的数据集管理操作有：
- 创建数据集
- 发起数据集发布任务
- 发起数据集导入任务
- 获取数据集详情
- 获取数据集状态详情
- 发起数据集导出任务
- 删除数据集
- 获取数据集导出记录
- 获取数据集导入错误详情

### Prompt 管理

千帆平台支持对文生文、文生图任务的 Prompt 进行管理，详见[Prompt 管理](./docs/prompt.md)

目前支持的 Prompt 管理操作有：

- 创建 Prompt
- 更新 Prompt
- 删除 Prompt
- 获取 Prompt 详情
- 获取 Prompt 列表
- 获取 Prompt 标签列表

### 其他
- [tokenizer](./docs/utils.md)
- [流量控制](./docs/configurable.md)


> Check [**API References**](https://qianfan.readthedocs.io/en/stable/qianfan.html) for more details.
## License

Apache-2.0
