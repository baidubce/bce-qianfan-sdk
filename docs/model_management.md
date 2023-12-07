# 模型管理

千帆平台提供 API 接口对模型进行管理，这部分操作鉴权与 SFT 大模型调优一致，需要提供 Access Key 和 Secret Key，详见 [官方文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

目前支持的模型管理操作有：

- [获取模型详情](#获取模型详情)
- [获取模型版本详情](#获取模型版本详情)
- [训练任务发布为模型](#训练任务发布为模型)
- [发起模型评估任务](#发起模型评估任务)
- [查看模型评估详情](#查看模型评估详情)
- [查看模型评估报告](#查看模型评估报告)
- [停止模型评估任务](#停止模型评估任务)

使用前需要引用入Model类
```python
from qianfan.resources import Model
```

#### **获取模型详情**

可以获得该模型的所有版本信息，需要提供模型的 id，可以从 [智能云千帆控制台-模型仓库列表](https://console.bce.baidu.com/qianfan/modelcenter/model/user/list) 获得，详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clnlizwcs)。

```python
model_list = Model.list(model_id = 5862)
print(model_list['result']['modelVersionList'][0]['modelName'])
```

#### **获取模型版本详情**

可以获取某个模型版本的具体信息，需要提供模型版本 id，可以从 [智能云千帆控制台-模型仓库列表](https://console.bce.baidu.com/qianfan/modelcenter/model/user/list) 的某个模型详情中获得，详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ylnljj3ku)。

```python
model = Model.detail(model_version_id = 5659)
print(model['result']['modelName'])
```

#### **训练任务发布为模型**

可以将某个已完成的训练任务得到的模型发布至模型仓库中，需要提供任务 id 等信息，字段定义与返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Jlnlm0rdx)。

```python
g = Model.publish(
    is_new=True,
    model_name="sdk_test_1",
    version_meta={"taskId": 9220, "iterationId": 5234},
)
print(g['result']['modelId'])
```

#### **发起模型评估任务**

可以通过此函数在平台上发起一个模型评估任务，具体字段定义和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlpbyhl9o)。

```python
t = Model.create_evaluation_task(
    "test_name_only_rule",
    [
        {
            "modelId": 2259,
            "modelVersionId": 2744,
        },
        {
            "modelId": 2258,
            "modelVersionId": 2743,
        },
    ],
    14666,
    {
        "evalMode": "rule",
        "scoreModes": [
            "similarity",
            "accuracy",
        ],
    },
    dataset_name="CMMLU_STEM"
)
print(t['result'])
```

#### **查看模型评估详情**

通过这个方法查询模型评估任务的详情，需要提供评估任务的 ID `eval_id`。具体字段定义和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/wlpbyj1dn)。

```python
t = Model.get_evaluation_info(eval_id=14670)
print(t['result'])
```

#### **查看模型评估报告**

通过这个方法查询模型评估任务的结果报告，需要提供评估任务的 ID `eval_id`。具体字段定义和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/7lpbyk8fj)。

```python
t = Model.get_evaluation_result(eval_id=14670)
print(t['result'])
```

#### **停止模型评估任务**

通过这个方法停止模型评估任务，需要提供评估任务的 ID `eval_id`。具体字段定义和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/klpbyl1ea)。

```python
t = Model.stop_evaluation_task(eval_id=14670)
print(t['result'])
```