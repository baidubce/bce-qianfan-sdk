### 模型调优

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
resp = FineTune.create_task(
    name="task_name", 
    description="task_desc",
    base_train_type="ERNIE-Bot-turbo",
    train_type="ERNIE-Bot-turbo-0725",
)
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


