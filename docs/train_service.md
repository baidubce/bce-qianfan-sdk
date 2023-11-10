# 训练与服务
### 大模型调优
目前千帆平台支持如下 
SFT 相关操作：
- [创建训练任务](#创建训练任务)
- [创建任务运行](#创建任务运行)
- [获取任务运行详情](#获取任务运行详情)
- [停止任务运行](#停止任务运行)

使用前需要引用入FineTune类
```python
from qianfan.resources import FineTune
```

#### **创建训练任务**

需要提供任务名称 `name` 和任务描述 `description`，返回结果在 `result` 字段中，具体字段与 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/almrgn397#body%E5%8F%82%E6%95%B0) 一致。

```python
# 创建任务
resp = FineTune.create_task(name="task_name", description="task_desc")
# 获取返回结果
task_id = resp['result']['id']
print(task_id)
```

#### **创建任务运行**

需要提供该次训练的详细配置，例如模型版本、数据集等等，且不同模型的参数配置存在差异，具体参数可以参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mlmrgo4yx#body%E5%8F%82%E6%95%B0)。

```python
# 创建任务运行，具体参数可以参见 API 文档
create_job_resp = FineTune.create_job({
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

#### **获取任务运行详情**

需要提供任务和运行的 id，返回结果在 `result` 字段中，具体字段与 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/wlmrgowee#body%E5%8F%82%E6%95%B0) 一致。

```python
# 根据任务和运行id，查询任务运行的具体状态
job= FineTune.get_job(task_id, job_id)
# 获取任务详情
print(job['result'])
```

#### **停止任务运行**

需要提供任务和运行的 id，返回结果在 `result` 字段中，字段与 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lnlebz15#body%E5%8F%82%E6%95%B0) 一致。

```python
# 提供任务和运行 id，停止运行
stop = FineTune.stop_job(task_id, job_id)
# 获取停止结果
print(stop['result']) # => True
```

### 大模型管理

千帆平台提供 API 接口对模型进行管理，这部分操作鉴权与 SFT 大模型调优一致，需要提供 Access Key 和 Secret Key，详见 [官方文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

目前支持的模型管理操作有：

- [获取模型详情](#获取模型详情)
- [获取模型版本详情](#获取模型版本详情)
- [训练任务发布为模型](#训练任务发布为模型)

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

### 大模型服务

千帆平台提供 API 接口对大模型服务进行管理，这部分操作鉴权与 SFT 大模型调优一致，需要提供 Access Key 和 Secret Key，详见 [官方文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

目前支持的服务管理操作有：

- [创建服务](#创建服务)
- [查询服务详情](#查询服务详情)

使用前需要引用入Service类
```python
from qianfan.resources import Service
```

#### **创建服务**

可以将某个模型发布成可对外访问的服务，需要提供模型的 id、服务名称等信息，详细字段和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Plnlmxdgy)。

```python
g = Service.create(
    model_id=123,
    model_version_id=456,
    name="sdk_test",
    uri="svc_uri",
    replicas=1,
    pool_type=2,
)
print(g['result'])
```

#### **查询服务详情**
可以获取服务的具体信息，需要提供服务的 id，可以从 [百度智能云千帆控制台-服务管理](https://console.bce.baidu.com/qianfan/ais/console/onlineService) 的某个服务详情中获得，详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/llnlmyp8o)。

```python
svc = Service.get(id = 2047)
print(svc['result']['id'])
```