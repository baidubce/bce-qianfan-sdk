import sys
import pytest


def get_tool_list():
    from langchain.tools import tool

    @tool
    def paper_search(query: str, **kwargs) -> str:
        """using search engine to retrieve papers about your query"""
        if not query == "physics":
            raise ValueError(
                f"value retrieved from mock server isn't physics, rather: {query}"
            )

        return """
    Published: 2012-09-04
    Title: Is Physics Sick? [In Praise of Classical Physics]
    Authors: Hisham Ghassib
    Summary: In this paper, it is argued that theoretical physics is more akin to an
    organism than to a rigid structure.It is in this sense that the epithet,
    "sick", applies to it. It is argued that classical physics is a model of a
    healthy science, and the degree of sickness of modern physics is measured
    accordingly. The malady is located in the relationship between mathematics and
    physical meaning in physical theory.

    Published: 2000-02-10
    Title: Modern Mathematical Physics: what it should be?
    Authors: Ludwig Faddeev
    Summary: Personal view of author on goals and content of Mathematical Physics.

    Published: 2005-03-15
    Title: Topology in Physics
    Authors: R. Jackiw
    Summary: The phenomenon of quantum number fractionalization is explained. The
    relevance of non-trivial phonon field topology is emphasized.
        """

    return [paper_search]


@pytest.mark.skipif(sys.version_info < (3, 8, 1), reason="requires Python 3.8.1 or higher")
def test_sync_qianfan_single_agent():
    from langchain.agents import AgentExecutor
    from langchain.chat_models import QianfanChatEndpoint

    from qianfan.extensions.langchain.agents import (
        QianfanSingleActionAgent,
    )

    tools = get_tool_list()
    agent_qianfan = QianfanSingleActionAgent.from_system_prompt(
        tools, QianfanChatEndpoint(model="ERNIE-Bot-4")
    )
    agent_executor_qianfan = AgentExecutor(agent=agent_qianfan, tools=tools)
    assert agent_executor_qianfan.run("帮我搜索一篇 physics 领域的论文") == "测试成功"


@pytest.mark.skipif(sys.version_info < (3, 8, 1), reason="requires Python 3.8.1 or higher")
@pytest.mark.asyncio
async def test_async_qianfan_single_agent():
    from langchain.agents import AgentExecutor
    from langchain.chat_models import QianfanChatEndpoint

    from qianfan.extensions.langchain.agents import (
        QianfanSingleActionAgent,
    )

    tools = get_tool_list()
    agent_qianfan = QianfanSingleActionAgent.from_system_prompt(
        tools, QianfanChatEndpoint(model="ERNIE-Bot-4")
    )
    agent_executor_qianfan = AgentExecutor(agent=agent_qianfan, tools=tools)
    assert (
        await agent_executor_qianfan.arun("帮我搜索一篇 physics 领域的论文")
    ) == "测试成功"


@pytest.mark.skipif(sys.version_info < (3, 8, 1), reason="requires Python 3.8.1 or higher")
def test_sync_qianfan_multi_agent():
    from langchain.agents import AgentExecutor
    from langchain.chat_models import QianfanChatEndpoint

    from qianfan.extensions.langchain.agents import (
        QianfanMultiActionAgent,
    )

    tools = get_tool_list()
    agent_qianfan = QianfanMultiActionAgent.from_system_prompt(
        tools, QianfanChatEndpoint(model="ERNIE-Bot-4")
    )
    agent_executor_qianfan = AgentExecutor(agent=agent_qianfan, tools=tools)
    assert agent_executor_qianfan.run("帮我搜索一篇 physics 领域的论文") == "测试成功"


@pytest.mark.skipif(sys.version_info < (3, 8, 1), reason="requires Python 3.8.1 or higher")
@pytest.mark.asyncio
async def test_async_qianfan_multi_agent():
    from langchain.agents import AgentExecutor
    from langchain.chat_models import QianfanChatEndpoint

    from qianfan.extensions.langchain.agents import (
        QianfanMultiActionAgent,
    )

    tools = get_tool_list()
    agent_qianfan = QianfanMultiActionAgent.from_system_prompt(
        tools, QianfanChatEndpoint(model="ERNIE-Bot-4")
    )
    agent_executor_qianfan = AgentExecutor(agent=agent_qianfan, tools=tools)
    assert (
        await agent_executor_qianfan.arun("帮我搜索一篇 physics 领域的论文")
    ) == "测试成功"
