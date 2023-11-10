# 模型服务

千帆平台提供 API 接口对大模型服务进行管理，这部分操作鉴权与 SFT 大模型调优一致，需要提供 Access Key 和 Secret Key，详见 [官方文档](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。

目前支持的服务管理操作有：

- [创建服务](#创建服务)
- [查询服务详情](#查询服务详情)

使用前需要引用入Service类
```python
from qianfan.resources import Service
```

#### **创建服务**

可以将某个模型发布成可对外访问的服务，需要提供模型的 id、服务名称等信息，详细字段和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Plnlmxdgy)。

```python
g = Service.create(
    model_id=123,
    model_version_id=456,
    name="sdk_test",
    uri="svc_uri",
    replicas=1,
    pool_type=2,
)
print(g['result'])
```

#### **查询服务详情**
可以获取服务的具体信息，需要提供服务的 id，可以从 [百度智能云千帆控制台-服务管理](https://console.bce.baidu.com/qianfan/ais/console/onlineService) 的某个服务详情中获得，详细方法和返回参数字段参见 [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/llnlmyp8o)。

```python
svc = Service.get(id = 2047)
print(svc['result']['id'])
```