# 数据可视化洞察

在千帆 Python SDK 中，我们提供了图形化的界面供用户直观的浏览数据、根据条件进行筛选、对指定列进行指标统计。

# 使用方式

有两种方式可以启动数据的可视化洞察

## CLI 启动

这种方式允许用户使用 CLI 启动一个洞察进程并打开可视化的网页

```shell
qianfan dataset insight [OPTIONS] DATASET_FILE  
```

其中，`DATASET_FILE` 是你想要进行数据洞察的数据文件的路径，支持 json, csv, txt（不建议使用 jsonl 格式的对话数据集），以及包含这些文件类型的文件夹

如果传入的数据集是非 txt 格式的文件（即不是纯文本数据集），还可以通过 -c 指令指定需要进行数据分析的列，支持多列，以英文逗号（,）分割。例如

```shell
qianfan dataset insight -c "cl1,cl2,cl3" DATASET_FILE  
```

## 函数启动

当用户使用千帆 Python SDK 加载了一个 `Dataset` 对象之后，我们就可以调用该对象的 `show_in_data_insight_mode` 函数来进入洞察模式。

该函数的入参与 CLI 模式对齐，用户可以给 `column_names` 参数传入一个列表，来指定进行数据分析的列。

```python
from qianfan.dataset import Dataset

ds = Dataset.load(data_file="your/file/path")
ds.show_in_data_insight_mode(["cl1", "cl2", "cl3"])
```

# 界面介绍

<img width="1434" alt="截屏2024-06-04 22 10 35" src="https://github.com/baidubce/bce-qianfan-sdk/assets/56953648/b7918f22-c7ac-4419-89da-3c26fb9b4117">

## 左侧的筛选条件框

在左侧的筛选框中，用户可以输入一列或这多列的筛选条件，以在右侧的表格中过滤出具有匹配条件的数据集

筛选框中支持的过滤条件包括完全匹配（即匹配包含了整个文本的数据），或者输入正则表达式进行模式匹配

如果该列为数值列，则只支持等号匹配（==）

## 中间的图表

中间的三个图表分别表示被数据分析列在文本长度、字重复率和特殊字符率上的分布情况。其中每一列都代表在一个特定区间中，每个列所包含的数据条目数量

用户可以点击表格右上角的按钮方法

## 右侧的汇总表格和详细表格

右侧的两个表格，分别表示被分析列在三项指标上的均值，以及详细的总表。在其中，用户可以自由浏览单条数据的情况，或点击标题列进行排序浏览。

## 退出按钮

用户可以点击退出按钮来结束当前洞察进程