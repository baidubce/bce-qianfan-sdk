千帆 Python SDK 提供了本地进行数据集管理、处理的能力。现阶段支持的功能有：
+ 数据集管理
  + 文件系统
    + 从本地文件创建数据集
    + 将数据集导出到本地文件
  + 千帆平台
    + 在千帆平台创建数据集
    + 将千帆数据集导出到本地
    + 将本地数据集通过私人 BOS 存储上传到千帆平台
  + 内存
    + 从 Python 对象创建数据集
+ 数据集处理
  + 数据集检视
  + 数据集清洗
  + 数据集校验

# 数据集管理
    
千帆 Python SDK 现支持用户通过 SDK 对本地或千帆平台的数据集进行管理。

## 本地数据集

### 导入
用户可以通过 SDK，读取特定格式的文件，并且转换成内存中的数据集对象以供检视、清洗和转换。

```python
from qianfan.dataset.dataset import Dataset

dataset = Dataset.load(data_file="path/to/dataset_file.json")
print(dataset)
```

SDK 在读取数据集时，依赖文件后缀对文件类型做自动解析，目前 SDK 支持的文件后缀名包括：
  + json
  + jsonl
  + csv
  + txt

用户也可以传入 `FormatType` 对象来手动指定数据集的文件类型

```python
from qianfan.dataset.dataset import Dataset
from qianfan.dataset.data_source import FormatType

dataset = Dataset.load(
  data_file="path/to/dataset_file_without_suffix",
  file_format=FormatType.Json
)

print(dataset)
```

### 导出

和导入类似，用户可以通过 SDK 提供的 `save` 方法将数据集导出到本地文件中。

如果是从文件导入创建的数据集，直接执行 `dataset.save()` 会将数据集数据覆盖写入到导入时的文件

用户也可以传递 `data_file` 参数来指定导出到文件名和文件路径，同时可以传递 `file_format` 参数来指定导出的格式

```python
from qianfan.dataset.dataset import Dataset
from qianfan.dataset.data_source import FormatType

dataset = Dataset.load(
  data_file="path/to/dataset_file_without_suffix",
  file_format=FormatType.Json
)


dataset.save(
  data_file="another/path/to/local_file",
  file_format=FormatType.Csv
)
```

### 文件数据源

除了在 `load` 中传递文件路径创建数据集，SDK 还支持通过文件数据源 `FileDataSource` 来创建数据集。

创建和使用文件数据源的方式如下所示：

```python
from qianfan.dataset.dataset import Dataset
from qianfan.dataset.data_source import FileDataSource

file_source = FileDataSource(path="local_file.json")
dataset = Dataset.load(file_source)
```

`FileDataSource` 同样支持用户传递 `file_format` 自己手动指定文件类型

```python
from qianfan.dataset.data_source import FileDataSource, FormatType

file_source = FileDataSource(
  path="local_file",
  file_format=FormatType.Json
)
```

文件数据源同样可以作为 `save` 的参数，来指定导出的文件路径

```python
from qianfan.dataset.dataset import Dataset
from qianfan.dataset.data_source import FileDataSource, FormatType

file_source = FileDataSource(
  path="local_file",
  file_format=FormatType.Json
)

dataset = Dataset.load(
  data_file="path/to/dataset_file_without_suffix",
  file_format=FormatType.Json
)

dataset.load(file_source)
```
