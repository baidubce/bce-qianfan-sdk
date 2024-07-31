# 数据集

目前支持的数据集管理操作有：
- [创建数据集](#创建数据集)
- [发起数据集发布任务](#发起数据集发布任务)
- [发起数据集导入任务](#发起数据集导入任务)
- [获取数据集详情](#获取数据集详情)
- [获取数据集状态详情](#获取数据集状态详情)
- [发起数据集导出任务](#发起数据集导出任务)
- [删除数据集](#删除数据集)
- [获取数据集导出记录](#获取数据集导出记录)
- [获取数据集导入错误详情](#获取数据集导入错误详情)
- [创建数据清洗任务](#创建数据清洗任务)
- [查看数据清洗任务详情](#查看数据清洗任务详情)
- [查看清洗任务列表](#查看清洗任务列表)
- [删除数据清洗任务](#删除数据清洗任务)
- [创建数据增强任务](#创建数据增强任务)
- [查看增强任务列表](#查看增强任务列表)
- [查看数据增强详情](#查看数据清洗任务详情)
- [删除数据增强任务](#删除数据增强任务)
- [实体标注](#实体标注)
- [删除实体](#删除实体)
- [获取实体列表](#获取实体列表)

使用前需要引用入 `Data` 类
```python
from qianfan.resources import Data
```

#### **创建数据集**
可以创建数据集，需要提供数据集名称 `name` 、数据集类型 `data_set_type` 、数据集模板 `DataTemplateType` 等信息。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/qloic44vr)。

```python
resp = Data.create_bare_dataset(
    "test_dataset_name",
    DataSetType.TextOnly,
    DataProjectType.Conversation,
    DataTemplateType.NonSortedConversation,
    DataStorageType.PrivateBos,
    "bos_bucket_name",
    "bos_path",
)
print(resp['result'])
```

#### **发起数据集发布任务**
能够直接发布数据集，需要提供数据集 ID `dataset_id`。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Uloic6krs)。

```python
resp = Data.release_dataset(12)
print(resp['result'])
```

#### **发起数据集导入任务**
允许用户导入数据集，需要提供数据集 ID `dataset_id` 、数据源类型 `import_source` 、文件在远端的路径 `file_url` 等。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Yloic82qy)。

```python
resp = Data.create_data_import_task(
        dataset_id=1,
        is_annotated=True,
        import_source=DataSourceType.SharedZipUrl,
        file_url="1",
    )
print(resp['result'])
```

#### **获取数据集详情** 
可以获取到数据集的状态，需要提供数据集 ID `dataset_id` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Xloick80a)。

```python
resp = Data.get_dataset_info(12)
print(resp['result'])
```

#### **获取数据集状态详情** 
允许用户批量获取数据集的状态信息，需要提供数据集 ID 的列表 `dataset_id_list` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Sloicm9qz)。

```python
resp = Data.get_dataset_status_in_batch([12, 48])
print(resp['result'])
```

#### **发起数据集导出任务** 
允许用户用 SDK 发起数据集导出任务，需要提供数据集 ID `dataset_id` ，导出目的地类型 `export_destination_type` 等。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/bloicnydp)。

```python
resp = Data.create_dataset_export_task(
        dataset_id=12,
        export_destination_type=DataExportDestinationType.PrivateBos,
        storage_id="bucket_name",
    )
print(resp['result'])
```

#### **删除数据集** 
能够直接删除数据集，需要提供数据集 ID `dataset_id` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Oloicp6fk)。

```python
resp = Data.delete_dataset(12)
print(resp['result'])
```

#### **获取数据集导出记录** 
可以获取到成功导出的数据集下载地址，需要提供数据集 ID `dataset_id` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Zlonqgtw0)。

```python
resp = Data.get_dataset_export_records(12)
print(resp['result'])
```

#### **获取数据集导入错误详情** 
能够让用户清楚的知道导入任务失败的原因，需要提供数据集 ID `dataset_id` 和错误码 `error_code` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlonqulbq)。

```python
resp = Data.get_dataset_import_error_detail(12, 55)
print(resp['result'])
```

#### **创建数据清洗任务**
在千帆平台创建一个数据清洗任务，需要提供源数据集 ID `source_dataset_id` ，目标数据集 ID `destination_dataset_id` 和数据清洗使用的算子参数字典 `operations` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/8lp6irqen)

```python
resp = Data.create_dataset_etl_task(1, 2, {"clean": [], "filter": []})
print(resp['result'])
```

#### **查看数据清洗任务详情**
查看某一数据清洗任务的详情，需要提供数据清洗任务 ID `etl_id` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mlp6it4vd)

```python
resp = Data.get_dataset_etl_task_info(12)
print(resp['result'])
```

#### **查看清洗任务列表**
查看本账号下的数据清洗任务列表，可选参数有 `page_size` ，指定窗口大小，以及 `offset` 任务列表的起始位置偏移量。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/elp7myxvp)

```python
resp = Data.get_dataset_etl_task_list(1, 2)
print(resp['result'])
```

#### **删除数据清洗任务**
删除某一数据清洗任务，需要提供数据清洗任务 ID 列表 `etl_ids` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Glp6iu8ny)

```python
resp = Data.delete_dataset_etl_task([12])
print(resp['result'])
```

#### **创建数据增强任务**
在千帆平台创建一个数据增强任务，需要提供源数据集 ID `source_dataset_id` ，目标数据集 ID `destination_dataset_id` ，需要使用的大模型服务名 `service_name` ，对应的服务 url `service_url` ，应用 id `app_id` ，样本种子数 `num_seed_fewshot` ，生成实例数 `num_instances_to_generate` ，相似度阈值 `similarity_threshold`。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Dlp6iv0zw)

```python
import os
from qianfan import resources

# 使用安全认证AK/SK鉴权，通过环境变量方式初始化；替换下列示例中参数，安全认证Access Key替换your_iam_ak，Secret Key替换your_iam_sk
os.environ["QIANFAN_ACCESS_KEY"] = "your_iam_ak"
os.environ["QIANFAN_SECRET_KEY"] = "your_iam_sk"

resp = resources.Data.create_dataset_augmenting_task(
    name='aug_task_01',
    source_dataset_id="ds-in20jpw3if43xcpb",
    destination_dataset_id="ds-8r6y2are3bb54tkr",
    dev_api_id=1431,
    app_id=26217111,
    num_seed_fewshot=1,
    num_instances_to_generate=1,
    similarity_threshold=0.5,
)
print(resp.body)
```

#### **查看数据增强详情**
查看某一数据增强任务的详情，需要提供数据增强任务 ID `task_id` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Clp6iwiy9)

```python
resp = Data.get_dataset_augmenting_task_info(12)
print(resp['result'])
```

#### **查看增强任务列表**
查询本账号下的数据增强任务列表，可选参数有模糊搜索关键词 `keyword` ，是否按开始时间升序排序 `sorted_by_start_time_asc` ， 指定窗口大小 `page_size` ，以及任务列表的起始位置偏移量 `offset` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Flp7n9xmp)

```python
resp = Data.get_dataset_aug_task_list("key", False, 10, 2)
print(resp['result'])
```

#### **删除数据增强任务**
删除某一数据增强任务，需要提供数据增强任务 ID 列表 `task_ids` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/glp6iy6h3)

```python
resp = Data.delete_dataset_augmenting_task([12])
print(resp['result'])
```

#### **实体标注**
对数据集中的某一实体进行标注，需要提供实体 ID `entity_id` ，数据集 ID `dataset_id` ，标注内容 `content` 或图片标签 `labels`。详细方法和返回参数参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mlp6izcqr) 

```python
resp = Data.annotate_an_entity(
    "48dc586f7eb638457b826c02c1b868ef8ac8911b495504625a1ac824f9d38ff8_5f9ac12ca15e4c9c9351174942865e5a",
    12,
     [{
        "prompt": "请根据下面的新闻生成摘要, 内容如下:一辆小轿车，一名女司机，竟造成9死24伤。日前，深圳市交警局对事故进行通报：从目前证据看，事故系司机超速行驶且操作不当导致。目前24名伤员已有6名治愈出院，其余正接受治疗，预计事故赔偿费或超一千万元。\n生成摘要如下:",
        "response": [
            ["女司机疲劳驾驶导致9死24伤"]
        ]
    }]
)

print(resp['result'])
```

#### **删除实体**
使用实体 ID 删除数据集中的实体，需要提供实体 ID 列表 `entity_ids` 和数据集 ID `dataset_id` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ilp6j1rse)

```python
resp = Data.delete_an_entity(["48dc586f7eb638457b826c02c1b868ef8ac8911b495504625a1ac824f9d38ff8_5f9ac12ca15e4c9c9351174942865e5a"], 12)
print(resp['result'])
```

#### **获取实体列表**
获取数据集中的实体列表，需要提供数据集 ID `dataset_id` ，指定窗口大小 `page_size` ，任务列表的起始位置偏移量 `offset`。可选参数包括导入时间范围列表 `import_time_closure` ，标注时间范围列表 `annotating_time_closure` ，展示实体类型 `listing_type`，文生图标签 ID 字符串 `label_id_str` 。详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Ulp6j2yep)

```python
resp = Data.list_all_entity_in_dataset(12, 10, 1)
print(resp['result'])
```