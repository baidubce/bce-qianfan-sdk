# 大模型推理

+ [Chat 对话](#chat-对话)
+ [Completion 续写](#completion-续写)
+ [Embedding 向量化](#embedding-向量化)
+ [Plugin 插件调用](#plugin-插件)
+ [文生图](#文生图)
+ [批量推理](#批量推理)

#### **Chat 对话**

用户只需要提供预期使用的模型名称和对话内容，即可调用千帆大模型平台支持的，包括 ERNIE-Bot 在内的所有预置模型，如下所示：

```python
import qianfan
# 鉴权参数也可以通过函数参数传入，若已通过环境变量配置，则无需传入
chat_comp = qianfan.ChatCompletion(access_key="...", secret_key="...")

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
    print(resp)	                 # 打印输出
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

#### **Completion 续写**

对于不需要对话，仅需要根据 prompt 进行补全的场景来说，用户可以使用 `qianfan.Completion` 来完成这一任务。

```python
import qianfan
comp = qianfan.Completion()

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

#### **Embedding 向量化**

千帆 SDK 同样支持调用千帆大模型平台中的模型，将输入文本转化为用浮点数表示的向量形式。转化得到的语义向量可应用于文本检索、信息推荐、知识挖掘等场景。

```python
# Embedding 基础功能
import qianfan
emb = qianfan.Embedding()

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

#### **Plugin 插件**

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

#### **文生图**
千帆平台提供了热门的文生图功能，千帆SDK支持用户调用SDK来获取文生图结果，以快速集成多模态能力到大模型应用中。

以下是一个使用示例
```python
qfg = qianfan.Text2Image()
resp = qfg.do(prompt="Rag doll cat", with_decode="base64")
img_data = resp["body"]["data"][0]["image"]

img = Image.open(io.BytesIO(img_data))
```

#### **批量推理**

上述模型均提供了 `batch_do` 和异步的 `abatch_do` 方法，方便用户批量进行推理，并通过 `worker_num` 来控制并发量。

```python
prompt_list = ["你好", "很高兴认识你"]
# 所有模型传入的均为一个 List，但内部元素类型与模型类型相关
# 内部元素类型与 `do` 方法传入的参数类型一致
# 例如 ChatCompletion 则应该传入 List[Union[Dict, QfMessages]]
# 额外参数例如 `model` 等，与 `do` 方法可传入的参数和使用方法一致
task = Completion().batch_do(prompt_list, worker_num=10)
# 由于推理任务较为耗时，所以推理会在后台进行
# 返回的 task 是一个 Future 对象，可以通过它来获得任务运行状态
# 例如通过 resp.finished_count() 和 resp.total_count() 来获取已完成和总任务数
print("{}/{}".format(task.finished_count(), task.total_count())) # => 11/20
# SDK 会按照输入顺序进行批量推理
# 可以通过遍历的方式获取已完成任务的结果
for r in task:
    # 需要调用 r.result() 来显式等待某一条推理完成
    res = r.result()
    # 如果推理成功，res 是一个 QfResponse 对象
    # 否则会是一个 Exception 对象，用户需要进行错误处理
    if not isinstance(res, Exception):
        print(res)
# 也可以通过 resp.results() 来等待所有推理任务完成并获取所有结果
results = task.results()
# 或者仅等待所有任务完成，避免因返回的数据量较大导致过多的内存占用
# 之后可再采用上述遍历的方式逐个获取结果
task.wait()
# 结果与输入一一对应，如果推理成功那么结果与 `do` 返回类型一致
# 否则是一个 Exception 对象，用户需要进行错误处理
for prompt, result in zip(prompt_list, results):
    if not isinstance(result, Exception):
        print(prompt, result)


# 异步调用
results = await Completion().abatch_do(prompt_list, worker_num=10)
# 返回值为一个 List，与输入列表中的元素一一对应
# 正常情况下与 `ado` 返回类型一致，但如果发生异常则会是一个 Exception 对象
for prompt, result in zip(prompt_list, results):
    if not isinstance(result, Exception):
        print(prompt, result)
```
