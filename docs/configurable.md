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

如果用户调用的是 ERNIE 系列的模型，千帆 SDK 会自动从平台获取限流配置。
此时用户也可以自己指定限流配置，千帆 SDK 会取两者中较小的那一个。

如果用户使用的是第三方模型，则需要自行配置限流。

现在的限流配置包括两类三种：
+ 请求频率类：
  + `query_per_second` : 设置一个 QPS 限制，为正浮点数
  + `request_per_minute`: 设置一个 RPM 限制，会限制每分钟请求的次数，为正浮点数
  
  上述两种参数只能同时使用一个
+ 文字总量类：
  + `token_limit_per_minute` : 设置每分钟内可以消耗的 Token 总数，为正整数

用户可以在创建相关请求对象时，传入上述参数来设置限流配置，如：
```python
import qianfan
chat_comp = qianfan.ChatCompletion(
    request_per_minute=300,
    token_limit_per_minute=300000,
)
```

也可以通过系统环境变量来设置
```python
import os

os.environ["QIANFAN_RPM_LIMIT"] = "300"
os.environ["QIANFAN_QPS_LIMIT"] = "1"
os.environ["QIANFAN_TOKEN_LIMIT"] = "30000"
```

### request_id

千帆SDK支持对用户对接口请求进行track，可以传入`request_id`作为参数以标记一次resources api 调用， 并在返回值中的header `X-Baidu-Request-id` 得到相对应的`request_id`
不传入request的情况下，sdk将生成随机的request_id

示例如下：
```python
import qianfan 
chat_comp = qianfan.Completion()
resp = chat_comp.do(prompt="hi", request_id="sdk_req_01")
```