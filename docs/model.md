# Model

千帆SDK对模型管理能力进行了抽象和封装，开发者可以通过`qianfan.model`模块进行模型相关的管理，和批量推理等操作：

## 模型管理：

在[model_management](model_management.md)中我们可以通过基本的模型管理管控API进行模型的发布、查询等操作。简单来说，`model_id`贯穿了整个模型生命周期，在模型发布后，必须知道`model_id`才能进行后续的推理，评估，部署等操作。

而`Model`是千帆SDK对模型管理进行抽象和封装，开发者可以通过`Model`对象结合`Dataset`，`Evaluation`等模块实现批量推理，评估等逻辑。

一般来说`Model`对象可以通过以下方式获得：

1. 直接构造：
```python
from qianfan.model import Model

m = Model(id="amv-xx")
```
2. 通过`trainer.run()`完成训练之后直接通过`trainer.output`获得：
```python
trainer.run()
m = trainer.output["model"]
```


## 基于`Model`进行模型离线批量推理

千帆平台支持了基于模型的评估能力，开发者可以通过`Model`对象和`Dataset`对象（需要为千帆Dataset对象）直接发起批量推理任务，以下是一个例子：

```python
from qianfan.model import Model
from qianfan.dataset import Dataset

ds = Dataset.load(qianfan_dataset_version_id="ds-xx")
m = Model(id="amv-xx")

m.batch_inference(dataset=ds)
```

## 基于`Model`进行模型评估

千帆SDK支持了基于本地评估，千帆平台评估等多种方式的评估能力，囊括了包括大模型裁判员，基于规则评估，人工评估，OpenCompass评估等多种评估方式，开发者可以结合`Model`对象和`Evaluation`模型发起评估任务，以下是一个基于千帆平台的规则评估器进行模型评估的例子：

```python
from qianfan.dataset import Dataset
from qianfan.model import Model
from qianfan.evaluation.evaluator import QianfanRuleEvaluator
from qianfan.evaluation import EvaluationManager

ds = Dataset.load(qianfan_dataset_version_id="ds-xxx")
m = Model(id="amv-xx")

# 千帆平台规则评估器:
qianfan_evaluators = [
    QianfanRuleEvaluator(using_accuracy=True, using_similarity=True),
]
em = EvaluationManager(qianfan_evaluators=qianfan_evaluators)
result = em.eval([m], ds)
```

## 基于`Model`进行服务部署

千帆SDK支持了代码层面将模型的部署成服务的能力，开发者在训练后或是希望使用预置模型自行发布的服务的时候可以使用`Model.deploy()`完成，以下是一个使用预付费发布指定`model_id`模型服务的例子：

```python
from qianfan import ChatCompletion
from qianfan.model import Model, Service
from qianfan.model.consts import ServiceType
from qianfan.model.configs import DeployConfig, PaymentType

m = Model(id="amv-xxx")
#m.auto_complete_info() to fix if model id not found
sft_svc: Service = m.deploy(DeployConfig(
    name="your_service_name",
    endpoint_suffix="your_sdk_suffix",
    replicas=1, # 副本数， 与qps强绑定
    service_type=ServiceType.Chat,
    payment_type=PaymentType.Prepaid.value,
    months=1, # 预付费购买的时长
))

### 使用Service调用部署好的模型服务
problem="your problem"
#获取服务对象，即ChatCompletion等类型的对象
chat_comp: ChatCompletion = sft_svc.get_res()
sft_chat_resp = chat_comp.do(messages=[{"content": problem, "role": "user"}])
sft_chat_resp["result"]
```

## 基于`Model`进行模型压缩

千帆SDK支持了代码层面将模型进行压缩的能力，开发者在针对`训练后的模型`希望进行模型压缩以提高模型性能的场景，可以使用`Model.compress()`完成，以下是一个使用量化INT8-PTQ压缩指定`model_id`模型的例子：

```python
from qianfan.model import Model
from qianfan.resources.console import consts as console_consts

m: Model = Model(id="amv-ws1pi3cqx9m1")
new_model: Model = m.compress(
    strategy=console_consts.ModelCompStrategy.Quantization,
    weight=console_consts.ModelQuantizationWeight.INT8PTQ,
)
```

参数说明：
- strategy： 模型压缩策略，可选值如下：
    - Quantization：量化压缩策略
    - Sparsity：稀疏化压缩策略
- weight: 量化压缩配置，当strategy为Quantization时，该字段必填，可选值：
    - INT8-PTQ
    - W8A16C16
    - W4A16C16

具体的模型支持情况请参考：[模型压缩支持情况](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hliu6yf75#%E6%A8%A1%E5%9E%8B%E5%8E%8B%E7%BC%A9%E6%94%AF%E6%8C%81%E8%8C%83%E5%9B%B4)
