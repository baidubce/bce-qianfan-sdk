## 千帆 CLI

千帆 SDK 提供了 CLI 工具，方便在命令行中直接使用千帆平台各项功能。

**使用方法**:

```console
$ qianfan [OPTIONS] COMMAND [ARGS]...
```

**基础参数**:

> **IMPORTANT**：以下参数必须位于 command 命令之前，否则会被识别成命令的参数而无法生效。
>
> CLI 也同样支持使用 [环境变量](./configurable.md) 和 [.env 文件](https://github.com/baidubce/bce-qianfan-sdk/blob/main/dotenv_config_sample.env) 的形式配置参数。

* `--access-key TEXT`：百度智能云安全认证 Access Key，获取方式参考 [文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。
* `--secret-key TEXT`：百度智能云安全认证 Secret Key，获取方式参考 [文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。
* `--ak TEXT` [过时]：千帆平台应用的 API Key，仅能用于模型推理部分 API，获取方式参考 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake)。
* `--sk TEXT` [过时]：千帆平台应用的 Secret Key，仅能用于模型推理部分 API，获取方式参考 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake)。
* `--version`：打印版本信息。
* `--install-completion`：为当前 shell 安装自动补全脚本。
* `--show-completion`：展示自动补全脚本。
* `--help`：打印帮助文档。

**命令**:

* `chat` 对话
* `completion` 补全
* `txt2img` 文生图
* `dataset` 数据集

### chat 对话

![](./imgs/cli/chat.gif)

**用法**:

```console
$ qianfan chat [OPTIONS]
```

**Options 选项**:

* `--model TEXT`：模型名称  [default：ERNIE-Bot-turbo]
* `--endpoint TEXT`：模型的 endpoint
* `--multi-line / --no-multi-line`：多行模式，通过两次回车确认提交消息  [default：no-multi-line]
* `--help`：展示帮助文档

### completion 补全

![completion](./imgs/cli/completion.gif)

**用法**:

```console
$ qianfan completion [OPTIONS] MESSAGES...
```

**Arguments 参数**:

* `MESSAGES...`：需要补全的 prompt，支持传递多个 prompt 以表示对话历史，依次表示用户和模型的消息，必须为奇数  [required]

**Options 选项**:

* `--model TEXT`：模型名称  [default：ERNIE-Bot-turbo]
* `--endpoint TEXT`：模型的 endpoint
* `--plain / --no-plain`：普通文本模式，不使用富文本  [default：no-plain]
* `--help`：展示帮助文档

### txt2img 文生图

![txt2img](./imgs/cli/txt2img.gif)

**用法**:

```console
$ qianfan txt2img [OPTIONS] PROMPT
```

该命令依赖 [Pillow](https://pypi.org/project/Pillow/)，需要使用该功能的话可以通过 `pip install Pillow` 安装，具体参考 [Pillow 安装文档](https://pillow.readthedocs.io/en/latest/installation.html)。

**Arguments 参数**:

* `PROMPT`：生成图片的 prompt  [required]

**Options 选项**:

* `--negative-prompt TEXT`：生成图片的负向 prompt
* `--model TEXT`：使用的模型名称  [default：Stable-Diffusion-XL]
* `--endpoint TEXT`：使用的模型 endpoint
* `--output PATH`：输出的文件名称  [default：`%Y%m%d_%H%M%S.jpg`]
* `--plain / --no-plain`：普通文本模式，不使用富文本  [default：no-plain]
* `--help`：展示帮助文档

### dataset 数据集

**用法**:

```console
$ qianfan dataset [OPTIONS] COMMAND [ARGS]...
```

**Options 选项**:

* `--help`：展示帮助文档

**Commands 命令**:

* `predict`：调用大模型对数据集进行预测，并保存到本地文件。
* `save`：保存数据集至本地文件或平台。
* `view`：预览数据集内容。

#### predict 数据集预测

调用大模型对数据集进行预测，并保存到本地文件。

**用法**:

```console
$ qianfan dataset predict [OPTIONS] DATASET
```

**Arguments 参数**:

* `DATASET`：待预测的数据集。值可以是一个本地文件的路径，也可以是平台上的数据集链接 (格式为 `qianfan://{model_version_id}`)。  [required]

**Options 选项**:

* `--model TEXT`：预测用的模型名称，可以用 `qianfan chat --list-model` 获取模型列表。  [default：ERNIE-Bot-turbo]
* `--endpoint TEXT`：预测用的模型 endpoint，该选项会覆盖 `--model` 选项。
* `--output PATH`：输出的文件路径。  [default：`%Y%m%d_%H%M%S.jsonl`]
* `--input-columns TEXT`：输入的列名称。  [default：prompt]
* `--reference-column TEXT`：参考答案的列名称。
* `--help`：展示帮助文档。

### save 数据集保存

保存数据集至本地文件或平台。

**用法**:

```console
$ qianfan dataset save [OPTIONS] SRC [DST]
```

**Arguments 参数**:

* `SRC`：源数据集。值可以是一个本地文件的路径，也可以是平台上的数据集链接 (格式为 `qianfan://{model_version_id}`)。 [required]
* `[DST]`：目标数据集。如果值是一个本地文件路径，那么数据将保存至该文件中。或者可以提供一个已有的千帆数据集链接 (qianfan://{model_version_id})，那么数据将被追加至该数据集中。如果不提供该值，那么将会在平台上创建一个新的数据集，此时需要提供创建数据集所需的一些参数，具体见下文。

**Options 选项**:

* `--dataset-name TEXT`：新建数据集的名称，仅在不提供 `DST` 参数时需要。
* `--dataset-template-type [non_sorted_conversation|sorted_conversation|generic_text|query_set|text2_image]`：数据集的类型，仅在不提供 `DST` 参数时需要。  [default：non_sorted_conversation]
* `--dataset-storage-type [public_bos|private_bos]`：数据集存储的类型，仅在不提供 `DST` 参数时需要。  [default：private_bos]
* `--bos-path TEXT`：数据集保存在 BOS 上的路径，仅在保存至平台时需要。 (e.g. bos://bucket/path/)
* `--help`：展示帮助文档。

### view 数据集预览

预览数据集内容。

**用法**:

```console
$ qianfan dataset view [OPTIONS] DATASET
```

**Arguments 参数**:

* `DATASET`：待预览的数据集。值可以是一个本地文件的路径，也可以是平台上的数据集链接 (格式为 `qianfan://{model_version_id}`)。[required]

**Options 参数**:

* `--row TEXT`：待预览的数据集行。用 `,` 分隔数个行，用 `-` 表示一个范围。 (e.g. 1,3-5,12)
* `--column TEXT`：待预览的数据集的列。用 `,` 分隔每个列名称。 (e.g. prompt,response)
* `--help`：展示帮助文档。