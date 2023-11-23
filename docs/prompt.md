# Prompt

千帆平台提供对 Prompt 进行管理的接口，鉴权需要 Access Key 和 Secret Key，获取方式详见 [官方文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

目前支持的 Prompt 操作有：

- [创建 Prompt](#创建-prompt)
- [更新 Prompt](#更新-prompt)
- [渲染 Prompt 模版并获取详情](#渲染-prompt-模版并获取详情)
- [删除 Prompt](#删除-prompt)
- [获取 Prompt 列表](#获取-prompt-列表)
- [获取标签列表](#获取标签列表)

使用前需要先引入 `Prompt` 类：

```python
from qianfan.resources import Prompt
```

### 创建 Prompt

最简单的方式是直接使用 `Prompt.create` 方法，传入 Prompt 名称和模板内容即可创建 Prompt，模版中通过 `{}` 表示待填充的变量名。返回结果可以通过 `['result']['templateId']` 字段获取模板 ID。返回字段详见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlp7waib4)。

```python
resp = Prompt.create(
    name="example_prompt",
    # 变量必须字母开头，仅包含字母、数字和下划线，长度 2-30
    template="example template {var1}", 
)
print(resp['result']['templateId'])
```

SDK 也提供了其他参数，能够根据需求创建 Prompt，例如通过 `identifier` 字段指定识别变量的符号，示例如下

```python
from qianfan.consts import PromptFrameworkType

resp = Prompt.create(
    name="example_prompt",
    identifier="()", # 支持的标识符有 ()、[]、{}、(())、[[]]、{{}}
    template="template (v1) {v2} (v3)", # 由于指定了标识符，所以此处 v2 不是变量
    framework=PromptFrameworkType.CRISPE, # 指定框架类型
    variables=["v1"], # 指定变量，不指定则自动识别
    label_ids=[10, 20] # 指定该 Prompt 对应的标签，获取方式见下方 `获取标签列表`
)
```

Prompt 框架类型包括 

- `NotUse`（默认）：不使用框架
- `Basic`：通过指令、背景信息、补充数据、输出格式四个维度表述 Prompt，详见 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Zlo55g7t3)
- `CRISPE`：通过 **C**apacity and **R**ole 人设、**I**nsight 背景信息和上下文、**S**tatement 执行的任务、**P**ersonality 风格、**E**xperiment 实践几个维度表述 Prompt，详见 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlo56qd21)
- `Fewshot`：通过少数几个示例指导模型进行回答，详见 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ilommtfb1)

千帆还提供了针对文生图场景的 Prompt，与上述使用方式一致，区别在于额外提供了 `negative_templates` 和 `negative_variables` 字段，表示负面 Prompt，这一参数通过 `scene=PromptSceneType.Text2Image` 开启。

```python
from qianfan.consts import PromptSceneType

resp = Prompt.create(
    name="txt2img_prompt",
    identifier="{}", 
    template="template {v1}",
    scene=PromptSceneType.Text2Image, # 设定 Prompt 场景为文生图
    negative_template="negative prompt {v2} {v3}", # 负面 Prompt 列表
    negative_variables=["v2"] # 与 variables 相同，可以指定变量，不指定会自动识别
)
```

### 更新 Prompt

SDK 提供了根据 Prompt ID 更新 Prompt 的能力，示例如下，返回字段详见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/plp7tp3kx)。

```python
resp = Prompt.update(
    id = 10, # Prompt ID
    name="new_name", # 更新 Prompt 名称，可选
    label_ids=[10, 20] # 更新 Prompt 标签，可选
    template="new template {v1}", # 更新 Prompt 模板，可选
    identifier="{}", # 更新 Prompt 变量标识符，可选
    negative_template="new negative template {v2} {v3}", # 更新 Prompt 负面模板，可选
)
```

### 渲染 Prompt 模版并获取详情

通过传入 Prompt ID 和变量值，SDK 可以渲染 Prompt 模版并获取详情，返回字段详见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Olp7ysef9)。

```python
resp = Prompt.info(
    id=10, # Prompt ID
    var1="example", # 变量值
    var2="example"
)
print(resp['result']['content'])
```

### 删除 Prompt

通过传入 Prompt ID，SDK 可以删除 Prompt，返回字段详见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlp7tri81)。

```python
resp = Prompt.delete(id=10)
print(resp['result']) # => True
```

### 获取 Prompt 列表

SDK 提供了获取 Prompt 列表的接口，通过 `Prompt.list` 方法即可获取到 Prompt 列表，并可以通过 `name` 字段进行筛选。返回字段详见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ulp7tycbq)。

```python
from qianfan.consts import PromptType

resp = Prompt.list(
    offset=0, # 偏移量，可选，默认 0
    page_size=10, # 页大小，可选，默认 10
    name="example", # 筛选 Prompt 名称，可选
    label_ids=[10, 20] # 筛选 Prompt 标签，可选，为空表示不筛选
    type=PromptType.User # 筛选 Prompt 类型，可选，默认用户自制模版，Preset 表示预置模版
)
```

### 获取标签列表

SDK 提供了获取标签列表的接口，返回字段详见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/zlp7u6inp)

```python
resp = Prompt.list_labels(
    offset=0, # 偏移量，可选，默认 0
    page_size=10, # 页大小，可选，默认 10
)
```