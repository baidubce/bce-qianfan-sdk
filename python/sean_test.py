import os
from qianfan import resources

# 通过环境变量初始化认证信息
# 使用安全认证AK/SK调用，替换下列示例中参数，安全认证Access Key替换your_iam_ak，Secret Key替换your_iam_sk，如何获取请查看https://cloud.baidu.com/doc/Reference/s/9jwvz2egb
os.environ["QIANFAN_ACCESS_KEY"] = "your_iam_ak"
os.environ["QIANFAN_SECRET_KEY"] = "your_iam_sk"

resp = resources.console.utils.call_action(
    # 调用本文API，该参数值为固定值，无需修改；对应API调用文档-请求结构-请求地址的后缀
    "/v2/batchinference",
    # 调用本文API，该参数值为固定值，无需修改；对应API调用文档-请求参数-Query参数的Action
    "CreateBatchInferenceTask",
    # 请查看本文请求参数说明，根据实际使用选择参数；对应API调用文档-请求参数-Body参数
    {
        "name": "eb4-job4",
        "description": "desc",
        "endpoint": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro",
        "inferenceParams": {
            "temperature": 0.9,
            "top_p": 0.3
        },
        "inputBosUri": "bos:/sdc-default/zhxxxan/input",
        "outputBosUri": "bos:/sdc-default/zhaxxxan/output"
    }
)
print(resp.body)