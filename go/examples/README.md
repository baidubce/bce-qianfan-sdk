# 千帆 Go SDK 示例

本文件夹中包含一些示例程序，展示了如何使用千帆 Go SDK。

- [`stream_chat`](./stream_chat/main.go)：实现了简易的能够在命令行与 LLM 聊天的程序，并使用流式输出，加快响应速度。
- [`embedding_distance`](./embedding_distance/main.go)：展示了如何使用千帆提供的 Embedding 模型，并计算两个文本的余弦距离。
- [`list_models`](./list_model/main.go)：展示了如何获取所有可用的模型。
- [`function_call`](./function_call/main.go)：展示了如何使用模型 function call 能力。
- [`text_to_image`](./text_to_image/main.go)：展示了如何使用千帆平台提供的文生图模型。