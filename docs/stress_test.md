# LLM服务性能测试

千帆 Python SDK 提供了基于locust工具的对大模型服务进行快速压测以及性能评估的功能。
该功能入口在Dataset对象的stress_test方法中。

## 目录

- [启动压测](#启动压测)
- [方法参数](#方法参数)
- [数据格式](#数据格式)
- [输出内容](#输出内容)

## 启动压测

如果用户想要对大模型服务进行性能测试，需要在导入 `qianfan` 模块之前设置环境变量 `QIANFAN_ENABLE_STRESS_TEST` 为 `true`

然后准备好测试用的数据集。数据集就绪后，可调用数据集的stress_test接口启动压测任务。

以下为一个调用的示例：

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
    workers=1,
    spawn_rate=128,
    model="ERNIE-Bot",
    model_type="ChatCompletion"
    total_count = len(ds)
)

```
## 方法参数
stress_test支持以下参数：

- **workers (int)**：指定发压使用的worker数目，每个worker为1个进程；
- **users (int)**：指定发压使用的总user数，必须大于worker数目；每个worker负责模拟${users}/${workers}个虚拟用户；
- **runtime (str)**：指定发压任务的最大运行时间，格式为带时间单位的字符串，例如（300s, 20m, 3h, 1h30m）；压测任务启动后会一直运行到数据集内所有数据都请求完毕，或到达该参数指定的最大运行时间；该参数默认值为'0s'，表示不设最大运行时间；
- **spawn_rate (int)**：指定每秒启动的user数目；
- **model (str)**：指定需要压测服务的模型名称。该参数与endpoint只能指定一个；
- **endpoint (str)**：指定需要压测服务的url路径。该参数与model只能指定一个；
- **model_type (str)**：指定被测服务的模型类型。 目前只支持'ChatCompletion'与'Completion两类'；默认值为'ChatCompletion'；
- **hyperparameters (Optional[Dict[str, Any]])**：指定压测时使用的超参数；
- **total_count (int)**：传入压测时使用的数据集总条数；


## 数据格式
可用于stress_test的数据集目前支持以下三种格式：

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
运行结束后会输出任务的日志路径，以及整体的聚合数据。
整体聚合数据内容示例：

    QPS: 4.02
    RPM: 55.46
    Latency Avg: 3.61
    Latency Min: 2.45
    Latency Max: 4.7
    Latency 50%: 3.6
    Latency 80%: 4.2
    FirstTokenLatency Avg: 1.54
    FirstTokenLatency Min: 0.85
    FirstTokenLatency Max: 2.62
    FirstTokenLatency 50%: 1.6
    FirstTokenLatency 80%: 1.9
    InputTokens Avg: 78.0
    OutputTokens Avg: 49.6
    total_count: 11100
    success_count: 58
    failure_count: 11042
    total_time: 62.75
    SuccessRate: 0.52%

各项指标含义如下：

- **QPS**：服务每秒实际处理的请求数；
- **RPM**：每分钟实际处理的请求数；
- **Latency Avg/Min/Max/50%/80%**：全长时延的平均值/最小值/最大值/50分位值/80分位值；
- **FirstTokenLatency Avg/Min/Max/50%/80%**：首句时延的平均值/最小值/最大值/50分位值/80分位值；
- **InputTokens Avg**：单次请求输入的token长度平均值；
- **OutputTokens Avg**：单次请求输出的token长度平均值；
- **total_count/success_count/failure_count**：总请求数/成功请求数/失败请求数；
- **total_time**：总运行时间；
- **SuccessRate**：请求成功率；
