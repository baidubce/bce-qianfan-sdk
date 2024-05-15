# 搭配千帆 Python SDK 使用 Guidance

Guidance 是开源社区中专注于，对大模型的输出进行约束，使得输出更符合用户预期的第三方开源框架。目前千帆 Python SDK 已经自身的推理能力以拓展插件的形式提供给 Guidance 的用户，用户可以现可将 Guidance 的能力用于文心系列大模型上。

# 如何安装

用户需要安装千帆 Python SDK ，以及 Guidance

```shell
pip install qianfan guidance
```

# 如何使用

在安装之后，用户即可以导入来自 `qianfan.extensions.guidance` 的对象来在 Guidance 使用千帆的推理能力。

现阶段我们提供了两种推理模型 `QianfanAIChat` 与 `QianfanAICompletion`，分别对应于对话场景与单纯的补全场景使用。

对于对话场景：

```python
import os

from guidance import gen, user, assistant

from qianfan.extensions.guidance import QianfanAIChat

os.environ["QIANFAN_ACCESS_KEY"] = "YOUR_ACCESS_KEY"
os.environ["QIANFAN_SECRET_KEY"] = "YOUR_SECRET_KEY"

lm = QianfanAIChat()

with user():
    lm += "帮我想一首有关于花的诗歌"

with assistant():
    lm += gen()

print(lm)
```

对于续写场景：

```python
import os

from guidance import gen

from qianfan.extensions.guidance import QianfanAICompletion

os.environ["QIANFAN_ACCESS_KEY"] = "YOUR_ACCESS_KEY"
os.environ["QIANFAN_SECRET_KEY"] = "YOUR_SECRET_KEY"

lm = QianfanAICompletion()

print(lm + gen("委内瑞拉的首都是"))
```

# 初始化参数与超参的传递

目前 Guidance 扩展中的 `QianfanAIChat` 与 `QianfanAICompletion` 结构体，初始化函数可以接收的超参对齐千帆 Python SDK 的 `ChatCompletion` 与 `Completion` 结构体。用户可以通过命名参数的形式来传递它们。如：

```python
from qianfan.extensions.guidance import QianfanAIChat

# 使用模型名来初始化
lm = QianfanAIChat(model="ERNIE-4.0-8K")

# 使用 Endpoint 来初始化
lm = QianfanAIChat(endpoint="completions_pro")
```

由于 Guidance 本身并不支持通过 `gen` 等函数在大模型发起请求时传递额外的超参，因此用户需要在构造相关的千帆 Python SDK 对象时就将超参填写完整。

例如，我们设置请求时的温度，应该使用如下的方式设置：

```python
from qianfan.extensions.guidance import QianfanAIChat

lm = QianfanAIChat(temperature=0.5)
```