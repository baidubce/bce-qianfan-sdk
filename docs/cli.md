## CLI 命令行工具

千帆 SDK 提供了 CLI 工具，方便在命令行中直接使用千帆平台各项功能。

**使用方法**:

使用前需要配置鉴权相关信息，关于 Access Key 和 Secret Key 的获取方式参考 [文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。除了使用环境变量，也可以通过下方命令行参数传递，或者是通过当前文件夹的 [.env 文件](https://github.com/baidubce/bce-qianfan-sdk/blob/main/dotenv_config_sample.env) 配置。

```console
$ export QIANFAN_ACCESS_KEY=your-access-key
$ export QIANFAN_SECRET_KEY=your-secret-key
$
$ qianfan [OPTIONS] COMMAND [ARGS]...
```

**基础参数**:

> **IMPORTANT**：以下参数必须位于 command 命令之前，否则会被识别成命令的参数而无法生效。

* `--access-key TEXT`：百度智能云安全认证 Access Key，获取方式参考 [文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。
* `--secret-key TEXT`：百度智能云安全认证 Secret Key，获取方式参考 [文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。
* `--ak TEXT` [过时]：千帆平台应用的 API Key，仅能用于模型推理部分 API，获取方式参考 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake)。
* `--sk TEXT` [过时]：千帆平台应用的 Secret Key，仅能用于模型推理部分 API，获取方式参考 [文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake)。
* `--version -v`：打印版本信息。
* `--install-completion`：为当前 shell 安装自动补全脚本。
* `--show-completion`：展示自动补全脚本。
* `--help -h`：打印帮助文档。

**命令**:

* `chat` 对话
* `completion` 补全
* `txt2img` 文生图

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
* `--list-model -l`：打印支持的模型名称列表
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
* `--list-model -l`：打印支持的模型名称列表
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
* `--list-model -l`：打印支持的模型名称列表
* `--help`：展示帮助文档
