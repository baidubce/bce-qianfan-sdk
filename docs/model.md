# Model

千帆SDK对模型管理能力进行了抽象和封装，开发者可以通过`qianfan.model`模块进行模型相关的管理，和批量推理等操作：

## 模型管理：

在[model_management](model_management.md)中我们可以通过基本的模型管理管控API进行模型的发布、查询等操作。简单来说，`model_version_id`贯穿了整个模型生命周期，在模型发布后，必须知道`model_version_id`才能进行后续的推理，评估，部署等操作。

而`Model`是千帆SDK对模型管理进行抽象和封装，开发者可以通过`Model`对象结合`Dataset`，`Evaluation`等模块实现批量推理，评估等逻辑。

一般来说`Model`对象可以通过以下方式获得：

1. 直接构造：
```python
from qianfan.model import Model

m = Model(version_id="amv-xx")
```
2. 通过`trainer.run()`完成训练之后直接通过`trainer.output`获得：
```python
trainer.run()
m = trainer.output["model"]
```


## 基于`Model`进行批量推理

千帆平台支持了基于模型的评估能力，开发者可以通过`Model`对象和`Dataset`对象（需要为千帆Dataset对象）直接发起批量推理任务，以下是一个例子：

```python
from qianfan.model import Model
from qianfan.dataset import Dataset

ds = Dataset.load(qianfan_dataset_id="ds-xx")
m = Model(version_id="amv-xx")

m.batch_inference(dataset=ds)
```

## 基于`Model`进行评估

千帆SDK支持了基于本地评估，千帆平台评估等多种方式的评估能力，囊括了包括大模型裁判员，基于规则评估，人工评估，OpenCompass评估等多种评估方式，开发者可以结合`Model`对象和`Evaluation`模型发起评估任务，以下是一个基于千帆平台的规则评估器进行模型评估的例子：

```python
from qianfan.dataset import Dataset
from qianfan.model import Model
from qianfan.evaluation.evaluator import QianfanRuleEvaluator
from qianfan.evaluation import EvaluationManager

ds = Dataset.load(qianfan_dataset_id="ds-xxx")
m = Model(version_id="amv-xx")

# 千帆平台规则评估器:
qianfan_evaluators = [
    QianfanRuleEvaluator(using_accuracy=True, using_similarity=True),
]
em = EvaluationManager(qianfan_evaluators=qianfan_evaluators
em = EvaluationManager(
    qianfan_evaluators=qianfan_evaluators
    # local_evaluators=[...]
)
)
result = em.eval([m], ds)
```

## 基于`Model`进行部署

千帆SDK支持了代码层面将模型的部署成服务的能力，开发者在训练后或是希望使用预置模型自行发布的服务的时候可以使用`Model.deploy()`完成，以下是一个使用预付费发布指定`model_version_id`模型服务的例子：

```python
from qianfan import ChatCompletion
from qianfan.model import Model, Service
from qianfan.model.consts import ServiceType
from qianfan.resources.console.consts import DeployPoolType

m = Model(version_id="amv-xxx")
#m.auto_complete_info() to fix if model id not found
sft_svc: Service = m.deploy(DeployConfig(
    name="your_service_name",
    endpoint_suffix="your_sdk_suffix",
    replicas=1, # 副本数， 与qps强绑定
    pool_type=DeployPoolType.PrivateResource, # 私有资源池
    service_type=ServiceType.Chat,
    hours=1, # 预付费购买的时长
))

### 使用Service调用部署好的模型服务
problem="your problem"
#获取服务对象，即ChatCompletion等类型的对象
chat_comp: ChatCompletion = sft_svc.get_res()
sft_chat_resp = chat_comp.do(messages=[{"content": problem, "role": "user"}])
sft_chat_resp["result"]
```