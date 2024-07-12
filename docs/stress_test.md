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
- **runtime (str)**：指定发压任务的最大运行时间，格式为带时间单位的字符串，例如（300s, 20m, 3h, 1h30m）；压测任务启动后会一直运行到数据集内所有数据都请求完毕，或到达该参数指定的最大运行时间；该参数默认值为'0s'，表示不设最大运行时间；
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

## 数据格式
可用于压测的数据集目前支持以下三种格式：

jsonl格式示例

这种格式主要用于多轮对话的场景，其中一个括号就是一段对话。最后的回答会在输入中被忽略

    [{"prompt": "请根据下面的新闻生成摘要, 内容如下:新华社受权于18日全文播发修改后的《中华人民共和国立法法》，修改后的立法法分为“总则”“法律”“行政法规”“地方性法规、自治条例和单行条例、规章”“适用与备案审查”“附则”等6章，共计105条。\n生成摘要如下:"}]
    [{"prompt": "请根据下面的新闻生成摘要, 内容如下:一辆小轿车，一名女司机，竟造成9死24伤。日前，深圳市交警局对事故进行通报：从目前证据看，事故系司机超速行驶且操作不当导致。目前24名伤员已有6名治愈出院，其余正接受治疗，预计事故赔偿费或超一千万元。\n生成摘要如下:"}]

json格式示例
    
    [
        {"prompt": "地球的自转周期是多久？", "response": "大约24小时"},
        {"prompt": "人类的基本单位是什么？", "response": "人类"}
    ]

txt格式示例

    人体最重要的有机物质是什么？
    化学中PH值用来表示什么？
    第一个登上月球的人是谁？


## 输出内容
运行过程中会实时输出已发送请求的聚合指标。
运行结束后会输出整体的聚合数据，以及任务的日志路径。日志路径中的performance_table.html为压测结果的可视化表格。
整体聚合数据内容示例：

        user_num: 4
        worker_num: 2
        spawn_rate: 2
        model_type: ChatCompletion
        hyperparameters: None
        QPS: 1.16
        Latency Avg: 3.08
        Latency Min: 1.95
        Latency Max: 4.56
        Latency 50%: 3.0
        Latency 80%: 3.6
        FirstTokenLatency Avg: 0.74
        FirstTokenLatency Min: 0.0
        FirstTokenLatency Max: 2.15
        FirstTokenLatency 50%: 0.64
        FirstTokenLatency 80%: 0.8
        InputTokens Avg: 69.6
        OutputTokens Avg: 43.67
        TotalInputTokens Avg: 2088.0
        TotalOutputTokens Avg: 1266.33
        TotalQuery: 30
        SuccessQuery: 29
        FailureQuery: 1
        TotalTime: 28.63
        SuccessRate: 96.67%

各项指标含义如下：
- **user_num**: 压测使用的本轮user数，即本轮发压的并发数；
- **worker_num**: 压测使用的worker数目，即进程数；
- **spawn_rate**: 每秒启动的user数目；
- **model_type**: 被压测服务的模型类型；
- **hyperparameters**: 压测使用的超参数；
- **QPS**：服务每秒实际处理的请求数；
- **Latency Avg/Min/Max/50%/80%**：全长时延的平均值/最小值/最大值/50分位值/80分位值；
- **FirstTokenLatency Avg/Min/Max/50%/80%**：首句时延的平均值/最小值/最大值/50分位值/80分位值；
- **InputTokens Avg**：单次请求输入的token长度平均值；
- **OutputTokens Avg**：单次请求输出的token长度平均值；
- **TotalQuery/SuccessQuery/FailureQuery**：总请求数/成功请求数/失败请求数；
- **TotalTime**：总运行时间；
- **SuccessRate**：请求成功率；

## Q&A

- Q: 为什么要先执行`monkey.patch_all()`？
- A: 由于Locust中使用了gevent库来保证高并发性能，而gevent的高并发依赖于monkey patching的非阻塞I/O机制，但该机制在Notebook环境中默认未开启。因此，在开始测试前，需要进行monkey patching操作。这样做是为了确保整个环境，包括IPython/Jupyter自己的组件，都使用gevent兼容的非阻塞版本，从而避免因混合使用阻塞和非阻塞操作导致的不一致性和潜在的死锁问题。