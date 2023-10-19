# Release Note

## 0.0.7

Feature:
- 增加对 SFT 相关管控类 API 支持（`qianfan.FineTune`）
- 增加模型相关接口的限流功能
Bug修复：
- 修复使用Completion时，通过参数传递 AK、SK 仍会提示未找到 AK、SK 的问题
- 修复使用Completion时传model+endpoint导致异常的问题
优化：
- 对 Auth 模块进行重构，同时支持同步及异步请求
- 默认不再使用 ERNIE-Bot-SDK
- 更新错误码

## 0.0.6

Bug修复：

- 修复 Embedding 内置模型 endpoint 错误的问题
- 修复 Completion 同时提供 chat 模型和自定义 endpoint 时，无法正确使用 chat 模型进行模拟的问题
- 修复 QfMessage 没有正确处理 QfRole 的问题

## 0.0.5

> commit 149b5d76...01e68dce

Bug修复：
- 修复为同一个AK、SK第二次手动设置AccessToken时不生效的问题
- 重构重试逻辑
  - 修复API返回错误时，非高负载的错误异常未抛出的问题
  - 修复多次重试失败后，没有异常抛出的问题
- 修复打印 warn 和 error 级别日志时打印过多trace的问题
- 修复无法正确识别AccessTokenExpired错误的问题

Feature：
- QfMessage支持function_call类型的消息
- 增加控制SDK log级别的功能 qianfan.enable_log(logging.INFO)/ qianfan.disable_log()，默认 WARN 级别
- 增加对 EBSDK 是否安装的检测，若未安装则回退全部使用千帆SDK实现

周边工具相关：
- 单元测试
  - 切换至 pytest，对测试整体架构进行重构
  - 增加 mock_server 用于测试
  - 增加对 auth 相关的测试用例
  - 增加测试相关脚本
    - make test即可进行测试，并打印覆盖率的报告
- 构建相关
  - 采用 Poetry 进行包管理（pyproject.toml）
    - setuptools 被标记 depracated，新的python库（如langchain）都采用这一工具进行管理
    - 支持区分包的依赖和开发时的依赖
    - pypi上可以设置例如主页等更为详细的元信息
    - 包版本的设置统一在 pyproject.toml 文件中设置，代码中qianfan.__version__修改成动态获取
  - 增加构建脚本
    - make build即可生成whl以及文档，输出在 output 目录中
    - make doc可以生成文档
    - 流水线上构建可以产出产物
- 流水线相关
  - 支持流水线上进行单测（流水线python版本3.7，可测试兼容性）
  - 支持发布流水线
    - 拉出 release-{VERSION}分支后可手动触发