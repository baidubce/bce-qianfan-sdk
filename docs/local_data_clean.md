# 本地数据清理算子

在千帆 SDK 中，我们为开发者提供了一系列用于数据处理的预置算子，在降低开发者心智负担的前提下，开发者可以通过调用这些预置算子，来快速、低成本的完成数据处理工作。

这些数据处理算子可以分为两大类：处理算子与过滤算子
+ 处理算子：会对匹配条件的输入数据进行处理，对外返回经过处理后的数据
+ 过滤算子：会检查输入数据是否满足过滤条件，如果满足过滤条件，则将输入数据标记为删除

若要使用这些算子，只需要在代码中引用这些数据清洗算子

## 处理算子

待建设

## 过滤算子

用户可以这样使用一个数据过滤算子

```python
from qianfan.dataset import Dataset
from qianfan.dataset.local_data_operators import LocalCheckCharacterRepetitionFilter

ds = Dataset.load(data_file="your/dataset/path")

filter_operator = LocalCheckCharacterRepetitionFilter()

ds = ds.filter(filter_operator)
```

下表是当前 SDK 所内置的过滤算子列表

| **算子名称** | **算子类名**                                 | **作用**                                       |
|----------|------------------------------------------|----------------------------------------------|
| 文档字重复率算子 | LocalCheckCharacterRepetitionFilter      | 如果字重复率太高，意味着文档中重复的字太多，文档会被过滤掉，采用 ngram 算法实现  |
| 文档句长检测算子 | LocalCheckEachSentenceIsLongEnoughFilter | 检查文档中句子的长度，并且当低于某一定长度的句子的数量超过一定比例阈值时，过滤掉整篇文档 |
| 文档色情暴力词率检测算子 | LocalCheckFlaggedWordsFilter | 如果色情暴力词率太高，文档会被过滤掉 |
| 文档特殊字符率检测算子 | LocalCheckSpecialCharactersFilter | 如果特殊字符率太高，意味着文档中特殊字符太多，文档会被过滤掉 |
| 文档词数目检测算子 | LocalCheckWordNumberFilter | 词数目不在指定范围会被过滤掉，如中文[1,1000000] |
| 文档词重复率检测算子 | LocalCheckWordRepetitionFilter | 如果词重复率太高，意味着文档中重复的字太多，文档会被过滤掉 |
| 停用词频率检测算子 | LocalCheckStopwordsFilter | 检查文本中的停用词占全文的比例，如果超出一定阈值则过滤掉整个文本 |


### 过滤算子通用参数列表
+ filter_column：待过滤的数据列列名，如果是泛文本数据则不必填写
+ text_language（可选）：待处理文本的语言种类

### 过滤算子专有参数列表

+ 文档字重复率算子（LocalCheckCharacterRepetitionFilter）
  + character_repetition_length（可选）：Ngram 窗口长度
  + character_repetition_max_cutoff（可选）：重复率上限阈值
+ 文档句长检测算子（LocalCheckEachSentenceIsLongEnoughFilter）
  + short_sentence_max_cutoff（可选）：短句句长上限 
  + short_sentence_ratio_max_cutoff（可选）：短句占比上限阈值
+ 文档色情暴力词率检测算子（LocalCheckFlaggedWordsFilter）
  + sentence_piece_model_path：sentence piece 语言模型的模型文件路径
  + words_augmentation_group_sizes（可选）：文档词汇拓展的扫描窗口大小
  + words_augmentation_join_char（可选）：拓展词汇的连接字符串
  + flagged_words_max_cutoff（可选）：敏感词占比上限阈值
+ 文档特殊字符率检测算子（LocalCheckSpecialCharactersFilter）：
  + special_characters（可选）：特殊字符串列表
  + special_characters_max_cutoff（可选）：特殊字符串占比上限阈值
+ 文档词数目检测算子（LocalCheckWordNumberFilter）：
  + sentence_piece_model_path：sentence piece 语言模型的模型文件路径
  + number_words_min_cutoff（可选）：文档词数目下限
  + number_words_max_cutoff（可选）：文档词数目上限
+ 文档词重复率检测算子（LocalCheckWordRepetitionFilter）：
  + sentence_piece_model_path：sentence piece 语言模型的模型文件路径
  + word_repetition_length（可选）：Ngram 窗口长度
  + word_repetition_max_cutoff（可选）：词重复率上限阈值
+ 停用词频率检测算子（LocalCheckStopwordsFilter）：
  + sentence_piece_model_path：sentence piece 语言模型的模型文件路径
  + words_augmentation_group_sizes（可选）：文档词汇拓展的扫描窗口大小
  + words_augmentation_join_char（可选）：拓展词汇的连接字符串
  + stopwords_max_cutoff（可选）：停用词占比上限阈值

## Acknowledgement

我们借鉴了[BigScience-Workshop / Data prepation](https://github.com/bigscience-workshop/data-preparation/tree/main/preprocessing/training/01b_oscar_cleaning_and_filtering)的部分算子设计，在此对 BigScience-Workshop / Data prepation 作者及开源社区表示感谢。