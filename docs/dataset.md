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

使用前需要引用入Data类
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
        DataTemplateType.NonAnnotatedConversation,
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