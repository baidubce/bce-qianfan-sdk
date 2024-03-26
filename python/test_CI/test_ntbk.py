"""
    Unit test for notebooks
"""
import logging

import pytest


@pytest.mark.skip
@pytest.mark.parametrize(
    "file_reg,params_dict",
    [(
            '**/function_call.ipynb',
            {
                'test_var': "test_value"
            }
    )]
)
def test_demo(file_reg, params_dict, executor):
    """
    测试用例 demo

    Args:
        file_reg (str): 测试文件unix路径
        params_dict (dict): 参数字典
        executor (object): 执行器对象（fixture）

    Returns:
        None
    """
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [  # 分开写的好处是会被单独执行，一个测试有错误不会终止其他测试
        ('auto_truncate_msg.ipynb', {}),
        ('function_call.ipynb', {}),
        ('function_call_with_tool.ipynb', {}),
        ('langchain_sequential.ipynb', {}),
        ('prompt.ipynb', {}),
        ('text2image.ipynb', {}),
        ('hub.ipynb', {}),
        ('plugin.ipynb', {}),
        ('eb_search.ipynb', {}),
        ('offline_batch_inference.ipynb', {}),
        ('batch_prediction.ipynb', {}),
    ]
)
def test_common(file_reg, params_dict, executor):
    """
    测试用例 cookbook目录下的一级ntbk文件

    Args:
        file_reg (str): 测试文件unix路径
        params_dict (dict): 参数字典
        executor (object): 执行器对象（fixture）

    Returns:
        None
    """
    executor.prepare(file_reg, params_dict)
    executor.run(debug=True)


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('agents/langchain_agent_with_qianfan_llm.ipynb', {}),
        ('agents/qianfan_single_action_agent_example.ipynb', {}),
    ]
)
def test_agents(file_reg, params_dict, executor):
    """
    测试用例 agents目录下的ntbk文件

    Args:
        file_reg (str): 测试文件unix路径
        params_dict (dict): 参数字典
        executor (object): 执行器对象（fixture）

    Returns:
        None
    """
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('dataset/dataset101.ipynb', {}),
        ('dataset/how_to_use_qianfan_operator.ipynb', {}),
        ('dataset/batch_inference_using_dataset.ipynb', {}),
    ]
)
def test_datasets(file_reg, params_dict, executor):
    """
    测试用例 datasets目录下的ntbk文件

    Args:
        file_reg (str): 测试文件unix路径
        params_dict (dict): 参数字典
        executor (object): 执行器对象（fixture）

    Returns:
        None
    """
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        # ('RAG/**/deeplake_retrieval_qa.ipynb', {}),  # 暂不跑
        ('RAG/**/question_answering.ipynb', {}),
        # ('RAG/**/qianfan_baidu_elasticsearch.ipynb', {}),  # 暂不跑
        ('RAG/**/pinecone_qa.ipynb', {}),  # 暂不跑
    ]
)
def test_rag(file_reg, params_dict, executor):
    """
    测试用例 RAG目录下的ntbk文件

    Args:
        file_reg (str): 测试文件unix路径
        params_dict (dict): 参数字典
        executor (object): 执行器对象（fixture）

    Returns:
        None
    """
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('**/semantic_kernel/agent_with_sk.ipynb', {}),
        ('**/semantic_kernel/chatbot_with_sk.ipynb', {}),
        ('**/semantic_kernel/rag_with_sk.ipynb', {}),
    ]
)
def test_sk(file_reg, params_dict, executor):
    """
    测试用例 semantic_kernel相关的ntbk文件

    Args:
        file_reg (str): 测试文件unix路径
        params_dict (dict): 参数字典
        executor (object): 执行器对象（fixture）

    Returns:
        None
    """
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('evaluation/how_to_use_evaluation.ipynb', {}),
        ('evaluation/local_eval_with_qianfan.ipynb', {}),
        ('evaluation/opencompass_evaluator.ipynb', {}),
    ]
)
def test_evaluation(file_reg, params_dict, executor):
    """
    测试用例 evaluation目录下的ntbk文件

    Args:
        file_reg (str): 测试文件unix路径
        params_dict (dict): 参数字典
        executor (object): 执行器对象（fixture）

    Returns:
        None
    """
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('finetune/finetune_with_bos_and_evaluate.ipynb', {}),
        ('finetune/api_based_finetune.ipynb', {}),
        # ('finetune/trainer_finetune_event_resume.ipynb', {}),  # keyError
        ('finetune/trainer_finetune.ipynb', {})
        # 24/26 APIError: api return error, req_id: 3838549625 code: 500001, msg: param invalid

    ]
)
def test_finetune(file_reg, params_dict, executor):
    """
    测试用例 finetune目录下的ntbk文件

    Args:
        file_reg (str): 测试文件unix路径
        params_dict (dict): 参数字典
        executor (object): 执行器对象（fixture）

    Returns:
        None
    """
    executor.prepare(file_reg, params_dict)
    executor.run(debug=True)


@pytest.mark.skip
@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('wandb/wandb.ipynb', {}),  # 未通过
    ]
)
def test_wandb(file_reg, params_dict, executor):
    """
    测试用例 wandb目录下的ntbk文件

    Args:
        file_reg (str): 测试文件unix路径
        params_dict (dict): 参数字典
        executor (object): 执行器对象（fixture）

    Returns:
        None
    """
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.asyncio
def test_reg(cli_reg, cli_params, executor):
    if cli_reg == '':
        logging.warning(f'cli_path_reg is empty, skip test')
        return
    executor.prepare(cli_reg, cli_params)
    executor.run()
