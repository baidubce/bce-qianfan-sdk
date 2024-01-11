# Evaluation 评估组件

千帆 Python SDK 中集成了发起平台评估与在线评估的能力。
现阶段支持的功能包括了
+ 使用平台进行在线评估
+ 在本地进行离线评估


* [平台在线评估](#平台在线评估)
  + [千帆评估器](#千帆评估器)
* [本地离线评估](#本地离线评估)
  + [对 Service 进行评估](#对-service-进行评估)
  + [对 Model 进行评估](#对-model-进行评估)
  + [获取评估结果](#获取评估结果)

## 平台在线评估

千帆 Python SDK 中集成了发起平台在线评估的能力，用户可以便捷的在本地就对云端数据集和模型发起评估任务，而无需耗费任何本地资源运行耗时的评估流程，千帆 Python SDK 会帮你完成评估任务的全流程监控

下面展示了使用平台在线评估能力进行基于规则的评估和裁判员评估的最简示例代码，**目前在线评估能力只支持使用云端数据集对模型进行评估**

```python
from qianfan.dataset import Dataset
from qianfan.evaluation import EvaluationManager
from qianfan.evaluation.evaluator import QianfanRuleEvaluator, QianfanRefereeEvaluator
from qianfan.evaluation.consts import QianfanRefereeEvaluatorDefaultMetrics, QianfanRefereeEvaluatorDefaultSteps, QianfanRefereeEvaluatorDefaultMaxScore
from qianfan.model import Model

your_qianfan_dataset_id = 123
ds = Dataset.load(qianfan_dataset_id=your_qianfan_dataset_id, is_download_to_local=False)

user_app_id = 123

qianfan_evaluators = [
    QianfanRuleEvaluator(using_accuracy=True, using_similarity=True),
    QianfanRefereeEvaluator(
        app_id=user_app_id,
        prompt_metrics=QianfanRefereeEvaluatorDefaultMetrics,
        prompt_steps=QianfanRefereeEvaluatorDefaultSteps,
        prompt_max_score=QianfanRefereeEvaluatorDefaultMaxScore,
    ),
]

em = EvaluationManager(qianfan_evaluators=qianfan_evaluators)
result = em.eval([Model(id=2, version_id=7170)], ds)
```

由于现阶段无法从平台导出详细的评估报告，用户只能通过 `EvaluationResult` 对象的 `metrics` 成员查询整体的评估结果

```python
print(result.metrics)
```

### 千帆评估器

现在千帆 Python SDK 支持三种可用于平台在线评估的评估器，分别是：

+ `QianfanRefereeEvaluator`：使用千帆提供的大模型对推理结果进行自动评估，用户可以指定评估时使用的提示词，推理步骤等内容
+ `QianfanRuleEvaluator`：使用一定的评估规则来对推理结果进行评估，目前支持的规则有 `accuracy` 和 `similarity` 两种
+ `QianfanManualEvaluator`：在完成推理后，由用户在平台上手动对推理结果进行打分评估。

用户可以根据自己的需要选择不同的评估器，也可以组合使用多个评估器进行评估。

## 本地离线评估

除了在平台上进行评估之外，千帆 Python SDK 还实现了在本地对部署在千帆平台上的 Service，以及在千帆平台上训练的 Model 进行本地评估的能力。

如果用户想进行本地评估，用户只需要初始化本地评估使用的 `LocalEvaluator` 对象列表，并且传入到 `EvaluationManager` 中即可：

```python
local_evaluators = [
    # 在这里传入你所希望使用的本地评估器对象
]

em = EvaluationManager(local_evaluators=local_evaluators)
```

需要注意的是，目前千帆 Python SDK 并没有提供本地评估器的实现，用户需要自行实现评估器的逻辑。

但是，本地评估器支持使用来自 OpenCompass 的评估器，使用 `OpenCompassLocalEvaluator` 包装即可。

```python
from opencompass.openicl.icl_evaluator import AccEvaluator
from qianfan.evaluation.evaluator import OpenCompassLocalEvaluator

open_compass_evaluator = AccEvaluator()

local_evaluators = [OpenCompassLocalEvaluator(open_compass_evaluator=open_compass_evaluator)]
```

### 对 Service 进行评估

如果用户需要对千帆平台上的服务进行评估，只需要初始化一个 `Service` 对象，并且传入需要评估的数据集即可。

支持对用户自部署的服务和预置服务进行评估

```python
from qianfan.model import Service

# 如果是用户自部署的服务，需要传入 endpoint
your_service = Service(endpoint="your/endpoint")

# 如果是预置服务，可以选择传入预置服务的 endpoint 或者服务名
pre_build_service = Service(endpoint="eb-instant")

em = EvaluationManager(local_evaluators=local_evaluators)

result = em.eval([your_service], ds)
```

### 对 Model 进行评估

与在线评估一致，对 `Model` 进行离线评估需要数据集已经被上传到千帆平台成为云端数据集

```python
your_qianfan_dataset_id = 123
ds = Dataset.load(qianfan_dataset_id=your_qianfan_dataset_id, is_download_to_local=False)

em = EvaluationManager(local_evaluators=local_evaluators)
result = em.eval([Model(id=2, version_id=7170)], ds)
```

### 获取评估结果

在完成离线评估后，评估得到的数据集会被保存在返回的 `EvaluationResult` 对象的 `result_dataset` 成员中。`result_dataset` 是一个 `Dataset` 对象，用户可以自行对其进行预览、修改、导出等操作。

```python
result_ds = result.result_dataset

result_ds.save(data_file="your/file/path")
```