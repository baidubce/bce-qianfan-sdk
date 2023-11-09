## SDK 配置
- 接口流控

千帆 SDK 内设了多种参数供用户设置，目前支持如下三种配置方式，按优先级从低到高排序：

1. 从 DotEnv 文件中读取。参考配置文件以及参数类型[点此](https://github.com/baidubce/bce-qianfan-sdk/blob/main/dotenv_config_sample.env)。SDK 默认读取工作目录下的 `.env` 文件进行配置，用户可以在程序运行前设置环境变量 `QIANFAN_DOT_ENV_CONFIG_FILE` 来指定需要使用的配置文件。

2. 通过环境变量读取。可配置的参数与方式 1 相同。举个例子，在代码中，用户可以这么设置：
```python
# 通过环境变量传递
import os
os.environ["QIANFAN_ACCESS_KEY"]="..."
os.environ["QIANFAN_SECRET_KEY"]="..."
```

> **NOTE**: 如果在代码中使用**环境变量**进行配置，请在设置时，将相关**设置代码**置于**实际使用的代码**前：
> ```python
> import os
> import qianfan
> 
> # 这样设置的参数是生效的
> os.environ["QIANFAN_QPS_LIMIT"] = "1"
> qianfan.ChatCompletion()
> 
> # 这样设置的参数是不生效的
> qianfan.ChatCompletion()
> os.environ["QIANFAN_QPS_LIMIT"] = "1"
> ```

3. 在代码中通过 `get_config()` 获取全局配置单例，并直接修改字段值。这种方式的优先级最高，且设置即生效。
```python
import qianfan

config = qianfan.get_config()
config.AccessKey = "..."
config.SecretKey = "..."

chat_comp = qianfan.ChatCompletion()
```

### 接口流控
千帆 SDK 支持对用户接口的请求进行限流，以防止超额请求带来的潜在问题。
若用户有自行配置限流的需求，只需要在创建对象时传入名为 `query_per_second` 的浮点参数，或者设置名为 `QIANFAN_QPS_LIMIT` 的环境变量即可限制接口的请求 QPS

创建对象时传入的实参，其应用优先级高于环境变量。

一个构造案例如下所示
```python
import qianfan
chat_comp = qianfan.ChatCompletion(query_per_second=0.5)
```
