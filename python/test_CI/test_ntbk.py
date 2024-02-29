"""
    Unit test for notebooks
"""
import pytest


@pytest.mark.skip
@pytest.mark.parametrize(
    "file_reg,params_dict",
    [(
            '**/test_*.ipynb',
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
    executor.run(debug=True)


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [  # 分开写的好处是会被单独执行，一个测试有错误不会终止其他测试
        # ('batch_prediction.ipynb', {}),
        # ('function_call.ipynb', {}),
        # ('function_call_with_tool.ipynb', {}),
        # ('langchain_sequential.ipynb', {}),
        # ('prompt.ipynb', {}),
        ('text2image.ipynb', {}),
        # ('hub.ipynb', {}),
        # ('function_call.ipynb', {}),
        # ('eb_search.ipynb', {}),
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
    executor.run()


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
        ('RAG/**/deeplake_retrieval_qa.ipynb', {}),  # 暂不跑
        ('RAG/**/question_answering.ipynb', {}),
        ('RAG/**/qianfan_baidu_elasticsearch.ipynb', {}),  # 暂不跑
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
    executor.run(debug=True)


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
        # ('evaluation/how_to_use_evaluation.ipynb', {}),  # 28/36 Must pass at least one table
        # ('evaluation/local_eval_with_qianfan.ipynb', {}),  # 28/39 ArrowInvalid: Must pass at least one table
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
    executor.run(debug=True)


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('finetune/finetune_with_bos_and_evaluate.ipynb', {}),
        ('finetune/api_based_finetune.ipynb', {}),  # 鉴权不一致
        # ('finetune/trainer_finetune_event_resume.ipynb', {}),  # keyError

        # ('finetune/trainer_finetune.ipynb', {})
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
    executor.run(debug=True)
