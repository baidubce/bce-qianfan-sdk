# LLM服务性能测试

千帆 Python SDK 提供了基于locust工具的对大模型服务进行单轮/多轮快速压测以及性能评估的功能。
该功能入口在Dataset对象的stress_test方法以及multi_stress_test方法中。


两种方法的使用场景不同。stress_test方法用于单轮压测，multi_stress_test方法用于多轮压测。
> 当前在notebook环境中进行压测调用需要先设置环境变量，具体设置以及使用方法见下文。                                               

## 安装准备

压测需要使用以下方式进行依赖安装：
```bash
pip install 'qianfan[dataset_base]'
```
注意，由于locust的框架限制。建议您在Python3.9-3.12版本中运行压测代码。


## 目录

- [启动压测](#启动压测)
- [方法参数](#方法参数)
- [数据格式](#数据格式)
- [输出内容](#输出内容)

## 启动压测

### stress_test方法

以下为stress_test方法的示例代码：

Python环境：

```python

import os

os.environ['QIANFAN_ENABLE_STRESS_TEST'] = "true"

from qianfan.dataset import Dataset

os.environ["QIANFAN_ACCESS_KEY"] = "..."
os.environ["QIANFAN_SECRET_KEY"] = "..."

# 需要初始化一个数据集对象

ds = Dataset.load(data_file="...")

ds.stress_test(
    users=1,
    #model="ERNIE-Speed-8K",
    endpoint="YourEndpoint",
    model_type="ChatCompletion"
)

```

### multi_stress_test方法

接下来为multi_stress_test方法的示例代码：

Python环境：

```python

import os

os.environ['QIANFAN_ENABLE_STRESS_TEST'] = "true"

from qianfan.dataset import Dataset

os.environ["QIANFAN_ACCESS_KEY"] = "..."
os.environ["QIANFAN_SECRET_KEY"] = "..."

# 需要初始化一个数据集对象

ds = Dataset.load(data_file="...")

ds.multi_stress_test(
    origin_users=2,
    workers=2,
    spawn_rate=2,
    #model="ERNIE-Speed-8K,
    endpoint="YourEndpoint",
    model_type="ChatCompletion",
    runtime="10s",
    rounds=2,
    interval=2,
    first_latency_threshold = 2,
    round_latency_threshold = 30,
    success_rate_threshold = 0.8,
)

```

Notebook中需要首先配置的环境变量如下，其他运行代码同上：

```python
from gevent import monkey
monkey.patch_all()
```

## 方法参数
### stress_test支持以下参数：

- **workers (int)**：指定发压使用的worker数目，每个worker为1个进程，默认为1个进程；
- **users (int)**：指定发压使用的总user数，必须大于worker数目；每个worker负责模拟${users}/${workers}个虚拟用户；
- **runtime (str)**：指定发压任务的最大运行时间，格式为带时间单位的字符串，例如（300s, 20m, 3h, 1h30m）；压测任务启动后会一直运行到数据集内所有数据都请求完毕，或到达该参数指定的最大运行时间；该参数默认值为'0s'，表示不设最大运行时间；
- **spawn_rate (int)**：指定每秒启动的user数目；
- **model (str)**：指定需要压测服务的模型名称。该参数与endpoint只能指定一个；
- **endpoint (str)**：指定需要压测服务的url路径。该参数与model只能指定一个；
- **model_type (str)**：指定被测服务的模型类型。 目前只支持'ChatCompletion'与'Completion两类'；默认值为'ChatCompletion'；
- **hyperparameters (Optional[Dict[str, Any]])**：指定压测时使用的超参数；

### multi_stress_test方法支持以下参数：

- **workers (int)**：指定发压使用的worker数目，每个worker为1个进程，默认为1个进程；
- **origin_users (int)**：指定发压使用的初始user数，必须大于worker数目；每个worker负责模拟${users}/${workers}个虚拟用户；
- **runtime (str)**：指定发压任务的单轮最大运行时间，格式为带时间单位的字符串，例如（300s, 20m, 3h, 1h30m）；压测任务启动后会一直运行到数据集内所有数据都请求完毕，或到达该参数指定的最大运行时间；该参数默认值为'0s'，表示不设最大运行时间；
- **spawn_rate (int)**：指定每秒启动的user数目；
- **model (str)**：指定需要压测服务的模型名称。该参数与endpoint只能指定一个；
- **endpoint (str)**：指定需要压测服务的url路径。该参数与model只能指定一个；
- **model_type (str)**：指定被测服务的模型类型。 目前只支持'ChatCompletion'与'Completion两类'；默认值为'ChatCompletion'；
- **hyperparameters (Optional[Dict[str, Any]])**：指定压测时使用的超参数；
- **rounds (int)**：指定压测轮数；
- **interval (int)**：指定压测轮之间的加压并发数，比如interval=2，则在第1轮压测结束后，会在第2轮开始时，额外启动两个user的并发，以此类推；
- **first_latency_threshold (float)**：指定首句时延的阈值，超过该阈值会停止在本轮压测，单位为秒；
- **round_latency_threshold (float)**：指定全长时延的阈值，超过该阈值会停止在本轮压测，单位为秒；
- **success_rate_threshold (float)**：指定请求成功率的阈值，低于该阈值会停止在本轮压测，单位为百分比；

除了上述参数，`stress_test` 和 `multi_stress_test` 方法还支持传入 kwargs，用于设置底层用于压测的 `ChatCompletion` / `Completion` 对象：

```python
# 用户可以这样进行 V2 接口的压测
ds.stress_test(users=1, version="2", app_id='app-xxx', model="ernie-speed-8k")
```

## 数据格式
可用于压测的数据集目前支持以下三种格式：

### jsonl格式示例
#### 千帆对话数据格式
这种格式主要用于多轮对话的场景，其中一个括号就是一段对话。最后的回答会在输入中被忽略

    [{"prompt": "请根据下面的新闻生成摘要, 内容如下:新华社受权于18日全文播发修改后的《中华人民共和国立法法》，修改后的立法法分为“总则”“法律”“行政法规”“地方性法规、自治条例和单行条例、规章”“适用与备案审查”“附则”等6章，共计105条。\n生成摘要如下:"}]
    [{"prompt": "请根据下面的新闻生成摘要, 内容如下:一辆小轿车，一名女司机，竟造成9死24伤。日前，深圳市交警局对事故进行通报：从目前证据看，事故系司机超速行驶且操作不当导致。目前24名伤员已有6名治愈出院，其余正接受治疗，预计事故赔偿费或超一千万元。\n生成摘要如下:"}]

#### 原始请求body格式
除了千帆也支持body格式的数据集，其中每一行是一个完整的对话，格式如下：

    {"messages": [{"role": "user", "content": "第一篇：一个男人把你当情人，而不是老婆，会有的表现，别傻傻分不清楚\n\n\n\n爱情，对于很多人来说，是人生旅途中最美好的部分。\n\n然而，不是所有的爱都会以结婚作为最终的归宿。\n\n有的人在一起，可能是因为爱情，有的则可能仅仅因为需要。\n\n而在现实中，很多女性经常感到困惑，难以分辨伴侣对待她们的态度到底是把她们当作生命中的唯一，还是仅仅视为一段情欲关系中的临时伴侣。\n\n毕竟，爱情是两个人的事，而只有当两个人在感情中的角色和期待相互匹配时，这段关系才能健康发展。\n\n一、避免深度交流\n\n一个将你看作情人的男人往往回避与你进行深入的情感交流或计划未来。\n\n当一个男人无意与你共筑未来时，他可能更倾向于保持一种神秘和随性的关系，而不是深入地探讨两人的内心世界或未来计划。\n\n有关感情深度的讨论，如家庭、责任感以及对双方关系的承诺等，往往被巧妙地避开，他不愿深入探讨任何可能会让关系升级的话题。\n\n二、不愿意公开恋情\n\n如果一个男人更愿意保持你们关系的隐秘性，不愿在公开场合展示你们的恋情，这可能是他把你当情人、而非未来伴侣的迹象。\n\n著名作家简·奥斯汀说：\n\n真正的感情是无需用言语或显眼的行为来展现的。\n\n然而，当这种保密转向了极端，连最基本的公开场合认可都没有时，这种隐秘可能并非出自真爱的谨慎，而是对关系的不认真。\n"}], "stream": true, "safety_level": "none"}
    {"messages": [{"role": "user", "content": "---片段 [家族长:182211080351][小组长:(167703434311),(染星⭐️)][男用户:(350144632491),(吾乃非尤物)][房间名称：招活跃小组长][家族类型：王者]\n\n[SYS|SYS|系统][2024-04-26 01:02:06.299000]\t[用户117449032021 上麦]\n\n[SYS|SYS|系统][2024-04-26 01:11:10.526000]\t[用户350144632491 上麦]\n\n[SYS|SYS|系统][2024-04-26 01:18:03.180000]\t[用户346337274181 上麦]\n\n[117449032021|女嘉宾|芍药][2024-04-26 01:11:13] "}], "stream": true, "safety_level": "none"}

### json格式示例
    
    [
        {"prompt": "地球的自转周期是多久？", "response": "大约24小时"},
        {"prompt": "人类的基本单位是什么？", "response": "人类"}
    ]

### txt格式示例

    人体最重要的有机物质是什么？
    化学中PH值用来表示什么？
    第一个登上月球的人是谁？


## 输出内容
运行过程中会实时输出已发送请求的聚合指标。
运行结束后会输出整体的聚合数据，以及任务的日志路径。日志路径中的performance_table.html为压测结果的可视化表格。
整体聚合数据内容示例：

    user_num: 50
    worker_num: 50
    spawn_rate: 50
    model_type: Completion
    hyperparameters: None
    QPS: 3.63
    Latency Avg: 3.121617
    Latency Min: 0.742033
    Latency Max: 11.915927
    Latency 50%: 2.9
    Latency 80%: 4.0
    Latency 90%: 6.4
    Latency 95%: 6.7
    Latency 99%: 12.0
    FirstTokenLatency Avg: 0.457397
    FirstTokenLatency Min: 0.366038
    FirstTokenLatency Max: 0.757577
    FirstTokenLatency 50%: 0.44
    FirstTokenLatency 80%: 0.49
    FirstTokenLatency 90%: 0.54
    FirstTokenLatency 95%: 0.58
    FirstTokenLatency 99%: 0.76
    IntervalLatency Avg: 0.490564
    IntervalLatency Min: 0.000174
    IntervalLatency Max: 1.708265
    IntervalLatency 50%: 0.44
    IntervalLatency 80%: 0.76
    IntervalLatency 90%: 0.99
    IntervalLatency 95%: 1.1
    IntervalLatency 99%: 1.2
    InputTokens Avg: 6.38
    OutputTokens Avg: 72.22
    TotalInputTokens: 319.0
    TotalOutputTokens: 3611.0
    InputStringLength Avg :13.1
    OutputStringLength Avg :136.44
    TotalInputStringLength: 655.0
    TotalOutputStringLength: 6822.0
    OutputTokensPerSecond: 23.14
    OutputStringLengthPerSecond: 43.71
    SendQuery: 50
    SuccessQuery: 50
    FailureQuery: 0
    TotalQuery: 50
    TotalTime: 16.77
    SuccessRate: 100.0%

各项指标含义如下：
- **user_num**: 压测使用的本轮user数，即本轮发压的并发数；
- **worker_num**: 压测使用的worker数目，即进程数；
- **spawn_rate**: 每秒启动的user数目；
- **model_type**: 被压测服务的模型类型；
- **hyperparameters**: 压测使用的超参数；
- **QPS**：服务每秒实际处理的请求数；
- **Latency Avg/Min/Max/50%/80%**：全长时延的平均值/最小值/最大值/50分位值/80分位值；
- **FirstTokenLatency Avg/Min/Max/50%/80%**：首Token时延的平均值/最小值/最大值/50分位值/80分位值；
- **IntervalLatency Avg/Min/Max/50%/80%**：包间时延的平均值/最小值/最大值/50分位值/80分位值；
- **InputTokens Avg**：单次请求输入的token长度平均值；
- **OutputTokens Avg**：单次请求输出的token长度平均值；
- **InputStringLength Avg**：单次请求输入的字符串长度平均值；
- **OutputStringLength Avg**：单次请求输出的字符串长度平均值；
- **OutputTokensPerSecond**：每秒输出的 token 量平均值；
- **OutputStringLengthPerSecond**：每秒输出的字符串长度平均值；
- **TotalQuery/SuccessQuery/FailureQuery**：总请求数/成功请求数/失败请求数；
- **TotalTime**：总运行时间；
- **SuccessRate**：请求成功率；

## V2 压测

对于新推出的 V2 接口，我们也同步适配了压测功能。

对于使用 `stress_test` 与 `multi_stress_test` 方法进行压测的用户，只需要在调用时如[推理文档](inference.md#v2-版本)所述，传入 version 与 app_id 参数即可。

```python
import os

os.environ['QIANFAN_ENABLE_STRESS_TEST'] = "true"

from qianfan.dataset import Dataset

os.environ["QIANFAN_ACCESS_KEY"] = "..."
os.environ["QIANFAN_SECRET_KEY"] = "..."

# 需要初始化一个数据集对象

ds = Dataset.load(data_file="...")

ds.stress_test(
    users=1,
    model="ERNIE-Speed-8K",
    version="2",
    app_id='app-xxx',
)
```

> [!IMPORTANT]
> 
> V2 接口不支持使用 Endpoint 作为入参。如果需要使用 Endpoint 作为入参，请使用 V1 接口。

## Q&A

- Q: notebook环境中为什么要先执行`monkey.patch_all()`？
- A: 由于Locust中使用了gevent库来保证高并发性能，而gevent的高并发依赖于monkey patching的非阻塞I/O机制，但该机制在Notebook环境中默认未开启。因此，在开始测试前，需要进行monkey patching操作。这样做是为了确保整个环境，包括IPython/Jupyter自己的组件，都使用gevent兼容的非阻塞版本，从而避免因混合使用阻塞和非阻塞操作导致的不一致性和潜在的死锁问题。
