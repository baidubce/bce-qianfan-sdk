# 百度千帆大模型平台 SDK

[![PyPI version](https://badge.fury.io/py/qianfan.svg)](https://pypi.org/project/qianfan/) [![Documentation Status](https://readthedocs.org/projects/qianfan/badge/?version=stable)](https://qianfan.readthedocs.io/en/stable/qianfan.html)

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

在使用千帆 SDK 之前，用户需要在千帆平台上创建应用，以获得 API Key (**AK**) 和 Secret Key (**SK**)。AK 与 SK 是用户在调用千帆 SDK 时所需要的凭证。具体获取流程参见平台的[应用接入使用说明文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake)。

获取到 AK 和 SK 后，用户还需要传递它们来初始化千帆 SDK。 千帆 SDK 支持如下三种传递方式，按优先级从低到高排序：

```python
# 通过环境变量传递（作用于全局，优先级最低）
import os
os.environ["QIANFAN_AK"]="..."
os.environ["QIANFAN_SK"]="..."

# 或者通过内置函数传递（作用于全局，优先级大于环境变量）
import qianfan
qianfan.AK("...")
qianfan.SK("...")

# 或者构造时传递（仅作用于该对象，优先级最高）
import qianfan
chat_comp = qianfan.ChatCompletion(ak="...", sk="...")
```

## 功能

目前千帆 SDK 支持用户使用如下功能

+ Chat 对话
+ Completion 续写
+ Embedding 向量化
+ Plugin 插件调用
+ SFT 大模型调优

### Chat 对话

用户只需要提供预期使用的模型名称和对话内容，即可调用千帆大模型平台支持的，包括 ERNIE-Bot 在内的所有预置模型，如下所示：

```python
import qianfan
chat_comp = qianfan.ChatCompletion(ak="...", sk="...")

# 调用默认模型，即 ERNIE-Bot-turbo
resp = chat_comp.do(messages=[{
    "role": "user",
    "content": "你好"
}])

print(resp['body']['result'])
# 输入：你好
# 输出：你好！有什么我可以帮助你的吗？

# 指定特定模型
resp = chat_comp.do(model="ERNIE-Bot", messages=[{
    "role": "user",
    "content": "你好"
}])

# 指定自行发布的模型
resp = chat_comp.do(endpoint="your_custom_endpoint", messages=[{
    "role": "user",
    "content": "你好"
}])

# 也可以利用内置 Messages 简化多轮对话
# 下面是一个简单的用户对话案例，实现了对话内容的记录
msgs = qianfan.Messages()
while True:
    msgs.append(input())         # 增加用户输入
    resp = chat_comp.do(messages=msgs)
    print(resp)									 # 打印输出
    msgs.append(resp)            # 增加模型输出
```

目前，千帆大模型平台提供了一系列可供用户通过 SDK 直接使用的模型，模型清单如下所示：

- [ERNIE-Bot-4](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clntwmv7t)
- [ERNIE-Bot-turbo](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/4lilb2lpf) （默认）
- [ERNIE-Bot](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/jlil56u11)
- [BLOOMZ-7B](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Jljcadglj)
- [Llama-2-7b-chat](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Rlki1zlai)
- [Llama-2-13b-chat](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lki2us1e)
- [Llama-2-70b-chat](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/8lkjfhiyt)
- [Qianfan-BLOOMZ-7B-compressed](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/nllyzpcmp)
- [Qianfan-Chinese-Llama-2-7B](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Sllyztytp)
- [ChatGLM2-6B-32K](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Bllz001ff)
- [AquilaChat-7B](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ollz02e7i)

对于那些不在清单中的其他模型，用户可通过传入 `endpoint` 来使用它们。

除了通过  `do`  方法同步调用千帆 SDK 以外， SDK 还支持使用 `ado` 来异步调用千帆 SDK。在同步和异步的基础上，用户还可以传入 `stream=True` 来实现大模型输出结果的流式返回。示例代码如下所示：

```python
# 异步调用
resp = await chat_comp.ado(model="ERNIE-Bot-turbo", messages=[{
    "role": "user",
    "content": "你好"
}])
print(resp['body']['result'])

# 异步流式调用
resp = await chat_comp.ado(model="ERNIE-Bot-turbo", messages=[{
    "role": "user",
    "content": "你好"
}], stream=True)

async for r in resp:
    print(r['result'])
```

### Completion 续写

对于不需要对话，仅需要根据 prompt 进行补全的场景来说，用户可以使用 `qianfan.Completion` 来完成这一任务。

```python
import qianfan
comp = qianfan.Completion(ak="...", sk="...")

resp = comp.do(model="ERNIE-Bot", prompt="你好")
# 输出：你好！有什么我可以帮助你的吗？

# 续写功能同样支持流式调用
resp = comp.do(model="ERNIE-Bot", prompt="你好", stream=True)
for r in resp:
    print(r['result'])

# 异步调用
resp = await comp.ado(model="ERNIE-Bot-turbo", prompt="你好")
print(resp['body']['result'])

# 异步流式调用
resp = await comp.ado(model="ERNIE-Bot-turbo", prompt="你好", stream=True)
async for r in resp:
    print(r['result'])

# 调用非平台内置的模型
resp = comp.do(endpoint="your_custom_endpoint", prompt="你好")
```

### Embedding 向量化

千帆 SDK 同样支持调用千帆大模型平台中的模型，将输入文本转化为用浮点数表示的向量形式。转化得到的语义向量可应用于文本检索、信息推荐、知识挖掘等场景。

```python
# Embedding 基础功能
import qianfan
emb = qianfan.Embedding(ak="...", sk="...")

resp = emb.do(model="Embedding-V1", texts=["世界上最高的山"])
print(resp['data'][0]['embedding'])
# 输出：0.062249645590782166, 0.05107472464442253, 0.033479999750852585, ...]

# 异步调用
resp = await emb.ado(texts=[
    "世界上最高的山"
])
print(resp['data'][0]['embedding'])

# 使用非预置模型
resp = emb.do(endpoint="your_custom_endpoint", texts=[
    "世界上最高的山"
])
```

对于向量化任务，目前千帆大模型平台预置的模型有：

- [Embedding-V1](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/alj562vvu) （默认）
- [bge-large-en](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mllz05nzk)
- [bge-large-zh](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/dllz04sro)

### Plugin 插件

千帆大模型平台支持使用平台插件并进行编排，以帮助用户快速构建 LLM 应用或将 LLM 应用到自建程序中。在使用这一功能前需要先[创建应用](https://console.bce.baidu.com/qianfan/plugin/service/list)、设定服务地址、将服务地址作为参数传入千帆 SDK

```python
# Plugin 基础功能展示
plugin = qianfan.Plugin()
resp = plugin.do(endpoint="your_custom_endpoint", prompt="你好")
print(resp['result'])

# 流式调用
resp = plugin.do(endpoint="your_custom_endpoint", prompt="你好", stream=True)

# 异步调用
resp = await plugin.ado(endpoint="your_custom_endpoint", prompt="你好")
print(resp['result'])

# 异步流式调用
resp = await plugin.ado(endpoint="your_custom_endpoint", prompt="你好", stream=True)
async for r in resp:
    print(r)
```

### 大模型调优

SFT 相关操作使用“安全认证/Access Key”中的 Access Key ID 和 Secret Access Key 进行鉴权，无法使用获取Access Token的方式鉴权，相关 key 可以在百度智能云控制台中 [安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist) 获取，详细流程可以参见 [文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

鉴权方式除命名外，使用方法与上述 AK 与 SK 方式相同，提供如下三种方式

```python
# 通过环境变量传递（作用于全局，优先级最低）
import os
os.environ["QIANFAN_ACCESS_KEY"] = "..."
os.environ["QIANFAN_SECRET_KEY"] = "..."

# 或者通过内置函数传递（作用于全局，优先级大于环境变量）
import qianfan
qianfan.AccessKey("...")
qianfan.SecretKey("...")

# 或者调用相关接口时传递（仅作用于该请求，优先级最高）
import qianfan
task = qianfan.FineTune.create_task(ak="...", sk="...")
```

目前千帆平台支持如下 SFT 相关操作：
- 创建训练任务
- 创建任务运行
- 获取任务运行详情
- 停止任务运行

**创建训练任务** 需要提供任务名称 `name` 和任务描述 `description`，返回结果在 `result` 字段中，具体字段与 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/almrgn397#body%E5%8F%82%E6%95%B0) 一致。

```python
# 创建任务
resp = qianfan.FineTune.create_task(name="task_name", description="task_desc")
# 获取返回结果
task_id = resp['result']['id']
print(task_id)
```

**创建任务运行** 需要提供该次训练的详细配置，例如模型版本、数据集等等，且不同模型的参数配置存在差异，具体参数可以参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mlmrgo4yx#body%E5%8F%82%E6%95%B0)。

```python
# 创建任务运行，具体参数可以参见 API 文档
create_job_resp = qianfan.FineTune.create_job({
    "taskId": task_id,
    "baseTrainType": "ERNIE-Bot-turbo",
    "trainType": "ERNIE-Bot-turbo-0725",
    "trainMode": "SFT",
    "peftType": "LoRA",
    "trainConfig": {
        "epoch": 4,
        "learningRate": 0.00002,
        "batchSize": 4,
        "maxSeqLen": 4096
    },
    "trainset": [
        {
            "type": 1,
            "id": 1234
        }
    ],
    "trainsetRate": 20
})

# 获取运行 id
print(create_job_resp['result']['id'])
```

**获取任务运行详情** 需要提供任务和运行的 id，返回结果在 `result` 字段中，具体字段与 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/wlmrgowee#body%E5%8F%82%E6%95%B0) 一致。

```python
# 根据任务和运行id，查询任务运行的具体状态
job= qianfan.FineTune.get_job(task_id, job_id)
# 获取任务详情
print(job['result'])
```

**停止任务运行** 需要提供任务和运行的 id，返回结果在 `result` 字段中，字段与 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lnlebz15#body%E5%8F%82%E6%95%B0) 一致。

```python
# 提供任务和运行 id，停止运行
stop = qianfan.FineTune.stop_job(task_id, job_id)
# 获取停止结果
print(stop['result']) # => True
```

### 大模型管理

千帆平台提供 API 接口对模型进行管理，这部分操作鉴权与 SFT 大模型调优一致，需要提供 Access Key 和 Secret Key，详见 [SFT 部分介绍](#sft-大模型调优)。

目前支持的模型管理操作有：

- 获取模型详情
- 获取模型版本详情
- 训练任务发布为模型

**获取模型详情** 可以获得该模型的所有版本信息，需要提供模型的 id，可以从 [智能云千帆控制台-模型仓库列表](https://console.bce.baidu.com/qianfan/modelcenter/model/user/list) 获得，详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clnlizwcs)。

```python
model_list = qianfan.Model.list(model_id = 5862)
print(model_list['result']['modelVersionList'][0]['modelName'])
```

**获取模型版本详情** 可以获取某个模型版本的具体信息，需要提供模型版本 id，可以从 [智能云千帆控制台-模型仓库列表](https://console.bce.baidu.com/qianfan/modelcenter/model/user/list) 的某个模型详情中获得，详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ylnljj3ku)。

```python
model = qianfan.Model.detail(model_version_id = 5659)
print(model['result']['modelName'])
```

**训练任务发布为模型** 可以将某个已完成的训练任务得到的模型发布至模型仓库中，需要提供任务 id 等信息，字段定义与返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Jlnlm0rdx)。

```python
g = qianfan.Model.publish(
    is_new=True,
    model_name="sdk_test_1",
    version_meta={"taskId": 9220, "iterationId": 5234},
)
print(g['result']['modelId'])
```

### 大模型服务

千帆平台提供 API 接口对大模型服务进行管理，这部分操作鉴权与 SFT 大模型调优一致，需要提供 Access Key 和 Secret Key，详见 [SFT 部分介绍](#sft-大模型调优)。

目前支持的服务管理操作有：

- 创建服务
- 查询服务详情

**创建服务** 可以将某个模型发布成可对外访问的服务，需要提供模型的 id、服务名称等信息，详细字段和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Plnlmxdgy)。

```python
g = qianfan.Service.create(
    model_id=123,
    iteration_id=456,
    name="sdk_test",
    uri="svc_uri",
    replicas=1,
    pool_type=2,
)
print(g['result'])
```

**查询服务详情** 可以获取服务的具体信息，需要提供服务的 id，可以从 [百度智能云千帆控制台-服务管理](https://console.bce.baidu.com/qianfan/ais/console/onlineService) 的某个服务详情中获得，详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/llnlmyp8o)。

```python
svc = qianfan.Service.get(id = 2047)
print(svc['result']['id'])
```

### 接口流控
千帆 SDK 支持对用户接口的请求进行限流，以防止超额请求带来的潜在问题。
若用户有自行配置限流的需求，只需要在创建对象时传入名为 `query_per_second` 的浮点参数即可限制接口的请求 QPS

一个构造案例如下所示
```python
import qianfan
chat_comp = qianfan.ChatCompletion(query_per_second=0.5)
```

## License

Apache-2.0
