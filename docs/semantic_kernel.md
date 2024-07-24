# semantic_kernel

千帆SDK支持了SK的接入适配，开发者可以方便的在SK中集成千帆平台的大模型调用能力：
- QianfanChatCompletion 文本对话
- QianfanTextCompletion 文本续写
- QianfanTextEmbedding 文本向量化

## 快速开始
```python
from qianfan.extensions.semantic_kernel import (
    QianfanChatCompletion,
    QianfanChatRequestSettings,
)
import asyncio

TEST_MESSAGES = [{"role":"user", "content":"hi"}]

async def run_chat():
    qf_chat = QianfanChatCompletion(model="ERNIE-3.5-8K")
    # call chat with messages
    res = await qf_chat.complete_chat_async(
        TEST_MESSAGES,
        QianfanChatRequestSettings(temperature=0.95),
    )
    print(res)

    async for r in qf_chat.complete_chat_stream_async(
        TEST_MESSAGES, QianfanChatRequestSettings()
    ):
        print(r)

    # completion with ChatCompletion
    res = await qf_chat.complete_async(
        TEST_MESSAGES[-1]["content"], QianfanChatRequestSettings()
    )
    print(res)

    # streaming completion with ChatCompletion
    async for r in qf_chat.complete_stream_async(
        TEST_MESSAGES[-1]["content"], QianfanChatRequestSettings()
    ):
        print(r)


asyncio.run(run_chat())
```

## 结合Semantic Kernel框架
除了直接调用QianfanChatCompletion类的成员函数，我们也可以结合SemanticKernel中的Kernel，Skill一起使用:

```python
from qianfan.extensions.semantic_kernel import (
    QianfanChatCompletion,
)

# with kernel
import semantic_kernel as sk

kernel = sk.Kernel()
kernel.add_text_completion_service(
    "qianfan_comp", QianfanChatCompletion(model="ERNIE-3.5-8K"),
)

prompt = """{{$input}}
生成一段关于以上主题的笑话
"""

joke = kernel.create_semantic_function(prompt_template=prompt, temperature=0.2, top_p=0.5)

print(joke("尔滨"))
```