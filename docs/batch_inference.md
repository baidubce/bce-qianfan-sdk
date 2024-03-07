# 批量推理

在进行模型评估或其他任务时，通常需要对大量数据进行预测。然而，模型推理过程往往耗时较长，通过循环串行执行会增加整体时间成本，而并行执行则需要额外的开发工作。

SDK 提供了多种解决方案来应对这一场景，其中包括：

- 本地并行推理：利用 SDK 内置的批量推理功能，在本地通过并行调用模型接口实现高效的批量预测。
- 数据集评估：利用 SDK 的 Dataset 模块，调用平台提供的数据集评估功能，以便快速而有效地完成任务。
- 离线批量推理：对于时间要求不那么严格的场景，可以考虑利用平台提供的离线批量预测能力，以降低实时推理的负载压力。

## 本地并行推理

> [点此](https://github.com/baidubce/bce-qianfan-sdk/blob/main/cookbook/batch_prediction.ipynb) 查看 Cookbook

对于 SDK 提供的诸如 `ChatCompletion`、 `Completion`、 `Image2Text` 等模型，均提供了 `batch_do` 和异步的 `abatch_do` 方法，可以方便地实现并行推理。

参数与 `do` 和 `ado` 相同，唯一的区别是传入的输入是 `List` 类型，而非单个样本，而 `List` 内每个元素则与单条推理时相同。例如对于 `Completion` 模型，单条推理输入是 `str` 类型的 prompt，那么批量推理时输入为 `List[str]`。

```python
prompt_list = ["你好", "很高兴认识你"]
# 所有模型传入的均为一个 List，但内部元素类型与模型类型相关
# 内部元素类型与 `do` 方法传入的参数类型一致
# 例如 ChatCompletion 则应该传入 List[Union[Dict, QfMessages]]
# 额外参数例如 `model` 等，与 `do` 方法可传入的参数和使用方法一致
# worker_num 是一个可选参数，用于指定并行调用模型接口的线程数
task = Completion().batch_do(prompt_list, worker_num=10)
# 由于推理任务较为耗时，所以推理会在后台进行
# 返回的 task 是一个 Future 对象，可以通过它来获得任务运行状态
# 例如通过 resp.finished_count() 和 resp.total_count() 来获取已完成和总任务数
print("{}/{}".format(task.finished_count(), task.total_count())) # => 11/20
# SDK 会按照输入顺序进行批量推理
# 可以通过遍历的方式获取已完成任务的结果
for r in task:
    try:
        # 需要调用 r.result() 来显式等待某一条推理完成
        res = r.result()
        # 如果推理成功，res 是一个 QfResponse 对象
        # 否则会是一个 Exception 对象，用户需要进行错误处理
    except Exception as e:
        print(e)

# 也可以通过 task.results() 来等待所有推理任务完成并获取所有结果
results = task.results()
# 或者仅等待所有任务完成，避免因返回的数据量较大导致过多的内存占用
# 之后可再采用上述遍历的方式逐个获取结果
task.wait()
# 结果与输入一一对应，结果与 `do` 返回类型一致
# 如果某条记录运行时发生异常，那么对应的值将是运行时所抛出的异常对象
for prompt, result in zip(prompt_list, results):
    if isinstance(result, Exception):
        # 处理异常
    else:
        # 处理正常结果
        print(prompt, result)


# 异步调用
results = await Completion().abatch_do(prompt_list, worker_num=10)
# 返回值为一个 List，与输入列表中的元素一一对应
# 正常情况下与 `ado` 返回类型一致，但如果发生异常则会是一个 Exception 对象
for prompt, result in zip(prompt_list, results):
    if not isinstance(result, Exception):
        print(prompt, result)
```

## 数据集评估

> [点此](https://github.com/baidubce/bce-qianfan-sdk/blob/main/cookbook/dataset/batch_inference_using_dataset.ipynb) 查看 Cookbook

SDK 的 Dataset 模块提供了数据集评估功能，可以方便地完成批量推理任务。只需要将待预测的数据加载成 Dataset 对象，然后调用 `test_using_llm` 方法即可。

### 使用服务进行推理

Dataset 支持使用平台提供的服务进行批量推理，也可以使用用户自己已发布的服务。

```python
from qianfan.dataset import Dataset

# 将数据集加载成 Dataset 对象
ds = Dataset.load(...)

# 用户可以设置 service_model 为自己想要的模型名，来直接对数据进行批量推理，以 EB 4 为例
result = ds.test_using_llm(service_model="ERNIE-Bot-4")

# 用户还可以设置 service_endpoint 来使用预置或自己的服务。
result = ds.test_using_llm(service_endpoint="completions_pro")
```

拿到的 result 也是一个 Dataset 对象，可以继续使用千帆 Python SDK 进行后续处理，或者直接保存到本地。

```python
print(result.list(0)) # => {'prompt': xxx, 'llm_output': xxx}

dataset_save_file_path = "output_file.csv"

result.save(data_file=dataset_save_file_path)
```

### 使用模型进行推理

Dataset 还支持使用平台上预置的模型或者用户训练完成的模型进行批量推理，该功能依赖平台的数据集评估功能，因此数据集必须是已经在千帆平台上发布的数据集。

使用方法与上述类似，只需要在调用 `test_using_llm` 时传入模型版本 ID。

```python
# 加载千帆平台上的数据集
qianfan_ds = Dataset.load(qianfan_dataset_id=cloud_dataset_id)

result = qianfan_ds.test_using_llm(model_version_id="amv-qb8ijukaish3")
print(result[0])
```

## 离线批量推理

> [点此](https://github.com/baidubce/bce-qianfan-sdk/blob/main/offline_batch_inference.ipynb) 查看 Cookbook

对于时间要求不那么严格的场景，可以考虑使用平台提供的离线批量推理能力，减少推理的成本消耗。

离线批量推理分为创建任务和查询任务两个步骤。

**创建任务** 需要先将数据集保存至 BOS 上，文件格式如下

```
{"id": "1", "query": "地球的自转周期是多久？"}
{"id": "2", "query": "太阳系中最大的行星是哪颗？"}
{"id": "3", "query": "月亮是围绕地球还是围绕太阳运转的？"}
{"id": "4", "query": "水的化学式是什么？"}
{"id": "5", "query": "世界上最高的山是哪座？"}
```

之后通过就可以利用 SDK 发起一个离线推理任务

```python
from qianfan.resources.console.data import Data

task = Data.create_offline_batch_inference_task(
    name="task_name",  # 任务名称
    descrption="task_description",  # 任务描述，可选
    # 推理模型的链接
    endpoint="https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
    inference_params= {   # 模型推理参数
        "temperature": 0.5,
    },
    input_bos_uri="bos:/sdk_test/inference-input/",  # 输入文件在 BOS 的路径
    output_bos_uri="bos:/sdk-test/inference-output/"  # 输出文件在 BOS 的路径
)

# 返回的结果是任务的 ID
task_id = task['result']['taskId']
```

**获取任务状态** 只需要传入任务的 id 即可，便可以获取任务的相关参数，以及通过 `runStatus` 字段判断任务是否完成。

```python
from qianfan.resources.console.data import Data

task = Data.get_offline_batch_inference_task(task_id="task_id")

status = task['result']['runStatus'] # => Done / Running / Failed
```