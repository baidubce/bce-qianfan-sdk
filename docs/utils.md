# 辅助工具

### Tokenizer

对于大语言模型，一般有 token 长度的限制，我们提供了 `Tokenizer` 工具类，可以方便地对文本的 token 数量进行计算，SDK 可以本地进行估算或者调用 API 精确计算。

**本地估算** 使用方法如下，公式为 `汉字数+单词数*1.3`

```python
text = "这是待计算 token 数量的一段文本"
count = qianfan.Tokenizer.count_tokens(text) 
```

**远程精确计算** 依赖千帆平台所提供的 API。SDK 侧使用方法相同，仅需额外传入 `mode = "remote"`，但由于需要调用远程接口，所以请按照上文先设置好 AK 与 SK，或者在该函数中传入。

```python
count = qianfan.Tokenizer.count_tokens(text, mode = "remote", model='ernie-3.5-8k')
print(count) # => 18 
```
