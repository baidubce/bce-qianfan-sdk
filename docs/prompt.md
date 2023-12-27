# Prompt

千帆平台提供对 Prompt 进行管理的接口，鉴权需要 Access Key 和 Secret Key，获取方式详见 [官方文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

SDK 提供了 `Prompt` 类，可以方便快速地使用千帆的 Prompt 能力，也在 resources 包内提供了原始的 Prompt 接口供使用。

## Prompt 类

> 我们提供了 Prompt 的 [cookbook](https://github.com/baidubce/bce-qianfan-sdk/tree/main/cookbook/prompt.ipynb)，可以通过案例快速了解如何使用

可以通过如下方式引用

```
from qianfan.common import Prompt
```

### 快速使用

平台上预置的 Prompt 以及用户自定义的模型都可以在 [千帆控制台](https://console.bce.baidu.com/qianfan/prompt/template) 获得，之后可以在 SDK 的 hub 能力从平台快速获取 Prompt 对象，并进行渲染等操作。

```python
from qianfan.common.hub import hub

# 获取平台上的 Prompt，name 为控制台上显示的名称
p = hub.load("prompt/区域美食推荐")
# 第二个参数是 negative prompt，仅文生图场景使用，此处可忽略
prompt, _ = p.render(region="上海")

# 之后就可以将渲染后的结果送入模型进行推理
qianfan.Completion().do(prompt)

# 文生图的 Prompt 使用方法相同，具体类型可以从控制台查看
txt2img_prompt = hub.load("prompt/角色设计")
# 类型通过变量属性获取
from qianfan.consts import PromptSceneType
txt2img_prompt.scene_type == PromptSceneType.Text2Image # => True

prompt, negative_prompt = txt2img_prompt.render()
# 之后将 prompt 和 negative_prompt 送入模型进行推理
qianfan.Text2Image().do(
    prompt=prompt, 
    negative_prompt=negative_prompt
)
```

### 本地 Prompt

如果不想使用平台上的 Prompt，也可以直接使用 `template` 参数构造 Prompt 对象。

```python
p = Prompt(
    template="本地 prompt {var1}",
)

prompt, _ = p.render(var1="hello") # => 本地 prompt hello

# 文生图 Prompt 同样支持
prompt = Prompt(
    name="txt2img",
    template="txt2img template ((v1))",
    scene_type=PromptSceneType.Text2Image, 
    negative_template="negative template ((v3))", # 负向 prompt
    identifier="(())", # prompt 中变量的标识符
)
```

### 上传&更新 Prompt

通过 hub 能力可以将本地 Prompt 上传到平台，或者是更新已有的 Prompt。

```python
p = Prompt(
    template="本地 prompt {var1}",
)

# 对于平台上的 prompt 来说，name 是必须的，因此上传前必须先设置
p.name = "cookbook_prompt"
hub.push(p)

p.id # => 188
```

上传后就可以获得 Prompt 的 ID，之后可以通过 `id` 属性获取 Prompt 对象。

也可以对 prompt 进行更新后再推送至平台上进行更新。

```python
p.set_template("新的 Prompt {new_var}")
hub.push(p) # 更新至平台

print(p.variables) # => ['new_var']
print(p.render(new_var="hello")) # => 新的 Prompt hello
```

### 删除 Prompt

调用 `delete` 方法可以删除 Prompt，如果是本地 Prompt 或者预置 Prompt，那么该函数将没有作用，删除后 Prompt 仍可以本地使用。

```python
p = hub.load("prompt/cookbook_prompt")
p.delete()
```

### 保存&加载

SDK 提供了 `save_to_file` 方法，可以将 Prompt 保存保存至本地。 再次使用时，只需要通过 `from_file` 方法即可读取 Prompt。

```python
p = Prompt(template="这是一个用于{usage}的 Prompt")
p.save_to_file("test_prompt.tpl")

p = Prompt.from_file("test_prompt.tpl")
prompt, _ = p.render(usage="测试")
print(prompt) # => 这是一个用于测试的 Prompt
```

### 框架类型

为了能够让模型更好的理解输入，需要提供足够详细的信息，千帆提供了数个 Prompt 框架类型，能够帮助用户编写出足够高质量的 Prompt，目前 SDK 支持如下框架类型：

- `NotUse`（默认）：不使用框架
- `Basic`：通过指令、背景信息、补充数据、输出格式四个维度表述 Prompt，详见 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Zlo55g7t3)
- `CRISPE`：通过 **C**apacity and **R**ole 人设、**I**nsight 背景信息和上下文、**S**tatement 执行的任务、**P**ersonality 风格、**E**xperiment 实践几个维度表述 Prompt，详见 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlo56qd21)
- `Fewshot`：通过少数几个示例指导模型进行回答，详见 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ilommtfb1)

```python
# 引入 PromptFrameworkType
from qianfan.consts import PromptFrameworkType
from qianfan.common import Prompt

# Basic 类型
basic_prompt = Prompt.base_prompt(
    prompt="帮我写一个年终总结",
    background="今年个人业绩情况为{var}。",
    additional_data="要去做演讲，风格要简约。",
    output_schema="输出内容要有成绩总结、遗留问题、改进措施和未来规划4项。"
)
prompt = Prompt(
    template=basic_prompt,
    framework_type=PromptFrameworkType.Basic
)

# CRISPE 类型
crispe_prompt = Prompt.crispe_prompt(
    capacity="你现在是一个资深律师。",
    insight="最近你接了一个财务侵占的官司，涉案金额{money}元，你是受害人的辩护律师。",
    statement="请帮忙出一个法律公告，警示被告尽快偿还非法侵占的财务。",
    personality="公告内容要严谨严肃专业。",
    experiment="公告内容不宜超过800字。",
)
prompt = Prompt(
    template=crispe_prompt,
    framework_type=PromptFrameworkType.CRISPE
)

# Fewshot 类型
fewshot_prompt = Prompt.fewshot_prompt(
    prompt="现在在做一个数学计算游戏，请根据下述规则回答最后一个示例的问题",
    examples=[
        ("1 2","3"),
        ("2 3","5"),
        ("3 4","")
    ]
)
prompt = Prompt(
    template=fewshot_prompt,
    framework_type=PromptFrameworkType.Fewshot
)
```

## Prompt 接口

目前支持的 Prompt 操作有：

- [创建 Prompt](#创建-prompt)
- [更新 Prompt](#更新-prompt)
- [渲染 Prompt 模版并获取详情](#渲染-prompt-模版并获取详情)
- [删除 Prompt](#删除-prompt)
- [获取 Prompt 列表](#获取-prompt-列表)
- [获取标签列表](#获取标签列表)

使用前需要从 `resources` 中引入 `Prompt`，注意与上述 `Prompt` 位置不同，建议非必要请使用上述的 `Prompt` 类，使用体验更佳：

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

关于框架类型，参见 [框架类型](#框架类型) 一节。

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
