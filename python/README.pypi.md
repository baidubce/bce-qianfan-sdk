# 百度千帆大模型平台 SDK

[![LICENSE](https://img.shields.io/github/license/baidubce/bce-qianfan-sdk.svg)](https://github.com/baidubce/bce-qianfan-sdk/blob/master/LICENSE)
[![Release Notes](https://img.shields.io/github/release/baidubce/bce-qianfan-sdk)](https://github.com/baidubce/bce-qianfan-sdk/releases)
[![PyPI version](https://badge.fury.io/py/qianfan.svg)](https://pypi.org/project/qianfan/)
[![Documentation Status](https://readthedocs.org/projects/qianfan/badge/?version=stable)](https://qianfan.readthedocs.io/en/stable/README.html)
[![Feedback Issue](https://img.shields.io/badge/%E8%81%94%E7%B3%BB%E6%88%91%E4%BB%AC-GitHub_Issue-brightgreen)](https://github.com/baidubce/bce-qianfan-sdk/issues)
[![Feedback Ticket](https://img.shields.io/badge/%E8%81%94%E7%B3%BB%E6%88%91%E4%BB%AC-%E7%99%BE%E5%BA%A6%E6%99%BA%E8%83%BD%E4%BA%91%E5%B7%A5%E5%8D%95-brightgreen)](https://console.bce.baidu.com/ticket/#/ticket/create?productId=279)

[Documentation](https://qianfan.readthedocs.io/en/stable/README.html) | [GitHub](https://github.com/baidubce/bce-qianfan-sdk) | [Cookbook](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook) 

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

chat_comp = qianfan.ChatCompletion(model="ERNIE-4.0-8K")
resp = chat_comp.do(messages=[{
    "role": "user",
    "content": "你好，千帆"
}], top_p=0.8, temperature=0.9, penalty_score=1.0)

print(resp["result"])
```

除了通过环境变量设置外，千帆 SDK 还提供了 `.env` 文件和通过代码配置的方式，详细参见 [SDK 配置](https://qianfan.readthedocs.io/en/stable/docs/configurable.html) 部分。

除了模型调用外，千帆 SDK 还提供模型训练、数据管理等诸多功能，如何使用请参考 [SDK 使用文档](https://qianfan.readthedocs.io/en/stable/README.html)。

<details>
<summary> 其他认证方式 </summary>

> 这里是一些其他认证方式，请仅在无法获取 Access Key 与 Secret Key 时使用。这些认证方式已经过时，将在未来从 SDK 中移除。

API Key (**AK**) 和 Secret Key (**SK**）是用户在调用千帆模型相关功能时所需要的凭证。具体获取流程参见平台的[应用接入使用说明文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake)，但该认证方式无法使用训练、发布模型等功能，若需使用请使用 Access Key 和 Secret Key 的方式进行认证。在获得并配置了 AK 以及 SK 后，用户即可开始使用 SDK：

```python
import os
import qianfan

os.environ["QIANFAN_AK"]="..."
os.environ["QIANFAN_SK"]="..."

chat_comp = qianfan.ChatCompletion(model="ERNIE-4.0-8K")
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

千帆平台提供了大模型相关的诸多能力，SDK 提供了对各能力的调用，具体介绍可以查看 [SDK 文档](https://qianfan.readthedocs.io/en/stable/README.html) 或者 [GitHub 仓库](https://github.com/baidubce/bce-qianfan-sdk)。

- **大模型能力** [[Doc](https://qianfan.readthedocs.io/en/stable/docs/inference.html)][[GitHub](https://github.com/baidubce/bce-qianfan-sdk/blob/main/docs/inference.md)]
  - Chat 对话
  - Completion 续写
  - Embedding 向量化
  - Plugin 插件调用
  - Text2Image 文生图
- **模型调优** [[Doc](https://qianfan.readthedocs.io/en/stable/docs/train.html)][[GitHub](https://github.com/baidubce/bce-qianfan-sdk/blob/main/docs/train.md)]
- **模型管理** [[Doc](https://qianfan.readthedocs.io/en/stable/docs/model_management.html)][[GitHub](https://github.com/baidubce/bce-qianfan-sdk/blob/main/docs/model_management.md)]
- **模型服务** [[Doc](https://qianfan.readthedocs.io/en/stable/docs/service.html)][[GitHub](https://github.com/baidubce/bce-qianfan-sdk/blob/main/docs/service.md)]
- **数据集管理** [[Doc](https://qianfan.readthedocs.io/en/stable/docs/dataset.html)][[GitHub](https://github.com/baidubce/bce-qianfan-sdk/blob/main/docs/dataset.md)]
- **Prompt 管理** [[Doc](https://qianfan.readthedocs.io/en/stable/docs/prompt.html)][[GitHub](https://github.com/baidubce/bce-qianfan-sdk/blob/main/docs/prompt.md)]
- **其他**
  - Tokenizer [[Doc](https://qianfan.readthedocs.io/en/stable/docs/utils.html)][[GitHub](https://github.com/baidubce/bce-qianfan-sdk/blob/main/docs/utils.md)]
  - 接口流控 [[Doc](https://qianfan.readthedocs.io/en/stable/docs/configurable.html)][[GitHub](https://github.com/baidubce/bce-qianfan-sdk/blob/main/docs/configurable.md)]

> 还可以通过 [**API References**](https://qianfan.readthedocs.io/en/stable/qianfan.html) 查看每个接口的详细说明。

## 联系我们

如使用过程中遇到什么问题，或对SDK功能有建议，可通过如下方式联系我们

- [GitHub issues](https://github.com/baidubce/bce-qianfan-sdk/issues)
- [百度智能云工单](https://console.bce.baidu.com/ticket/#/ticket/create?productId=279) （百度专家即时服务）

## License

Apache-2.0
