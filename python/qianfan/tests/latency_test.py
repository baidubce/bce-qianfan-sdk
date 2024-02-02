from qianfan.resources import ChatCompletion

_TEST_MESSAGE = [
    {"role": "user", "content": "请问你是谁？"},
    {
        "role": "assistant",
        "content": (
            "我是百度公司开发的人工智能语言模型，我的中文名是文心一言，"
            "英文名是ERNIE-Bot，"
            "可以协助您完成范围广泛的任务并提供有关各种主题的信息，比如回答问题，"
            "提供定义和解释及建议。"
            "如果您有任何问题，请随时向我提问。"
        ),
    },
    {"role": "user", "content": "我在深圳，周末可以去哪里玩？"},
]


def test_latency():
    chat_comp = ChatCompletion()
    resp = chat_comp.do(_TEST_MESSAGE)
    assert resp.statistic is not None
    assert "request_latency" in resp.statistic
    assert "total_latency" in resp.statistic
    assert "first_token_latency" not in resp.statistic

    for s_resp in chat_comp.do(_TEST_MESSAGE, stream=True):
        assert "request_latency" in s_resp.statistic
        assert "total_latency" in s_resp.statistic
        assert "first_token_latency" in s_resp.statistic


async def test_async_latency():
    chat_comp = ChatCompletion()
    resp = await chat_comp.ado(_TEST_MESSAGE)
    assert resp.statistic is not None
    assert "request_latency" in resp.statistic
    assert "total_latency" in resp.statistic
    assert "first_token_latency" not in resp.statistic

    async for s_resp in chat_comp.do(_TEST_MESSAGE, stream=True):
        assert "request_latency" in s_resp.statistic
        assert "total_latency" in s_resp.statistic
        assert "first_token_latency" in s_resp.statistic
