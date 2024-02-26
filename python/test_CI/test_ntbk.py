import os
import pytest
from utils.cookbook_execute import CookbookExecutor

@pytest.fixture(scope='session', autouse=True)
def env_set(request):
    if request.config.getoption('--ak') != '':
        os.environ['QIANFAN_ACCESS_KEY'] = request.config.getoption("--ak")
    if request.config.getoption('--sk') != '':
        os.environ['QIANFAN_SECRET_KEY'] = request.config.getoption("--sk")
    if request.config.getoption('--keywords') != '{}':
        os.environ['KEYWORDS_DICT'] = request.config.getoption("--keywords")
    if request.config.getoption('--root-dir') != '':
        os.environ['ROOT_DIR'] = request.config.getoption("--root-dir")
    else:
        os.environ['ROOT_DIR'] = '../../..'

    other_env = [('RetryCount', '3'), ('QIANFAN_QPS_LIMIT', '1'), ('QIANFAN_LLM_API_RETRY_COUNT', '3')]
    for key, value in other_env:
        os.environ[key] = value

    yield
    if os.environ.get('QIANFAN_ACCESS_KEY'):
        del os.environ['QIANFAN_ACCESS_KEY']
    if os.environ.get('QIANFAN_SECRET_KEY'):
        del os.environ['QIANFAN_SECRET_KEY']
    if os.environ.get('KEYWORDS_DICT'):
        del os.environ['KEYWORDS_DICT']
    if os.environ.get('ROOT_DIR'):
        del os.environ['ROOT_DIR']
    for key, value in other_env:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="function")
def executor():
    with CookbookExecutor() as e:
        yield e


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
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [  # 分开写的好处是会被单独执行，一个测试有错误不会终止其他测试
        ('batch_prediction.ipynb', {}),
        ('function_call.ipynb', {}),
        ('function_call_with_tool.ipynb', {}),
        ('langchain_sequential.ipynb', {}),
        ('prompt.ipynb', {}),
        ('text2image.ipynb', {}),
        ('hub.ipynb', {}),
        ('function_call.ipynb', {}),
        ('eb_search.ipynb', {}),

    ]
)
def test_common(file_reg, params_dict, executor):
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
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('dataset/dataset101.ipynb', {}),
        ('dataset/how_to_use_qianfan_operator.ipynb', {}),
        ('dataset/batch_inference_using_dataset.ipynb', {}),
    ]
)
def test_datasets(file_reg, params_dict, executor):
    executor.prepare(file_reg, params_dict)
    executor.run()


# 测试含有async的datasets notebook
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('dataset/batch_inference_using_dataset.ipynb', {}),
    ]
)
async def test_datasets_async(file_reg, params_dict, executor):
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('RAG/**/deeplake_retrieval_qa.ipynb', {}),  # 未通过
        ('RAG/**/question_answering.ipynb', {}),
        ('RAG/**/qianfan_baidu_elasticsearch.ipynb', {}),  # 未通过
        ('RAG/**/pinecone_qa.ipynb', {}),  # 未通过
    ]
)
def test_rag(file_reg, params_dict, executor):
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
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        # ('evaluation/how_to_use_evaluation.ipynb', {}),  # 7/36 鉴权不通过
        ('evaluation/local_eval_with_qianfan.ipynb', {}),  # 28/39 ArrowInvalid: Must pass at least one table
    ]
)
def test_evaluation(file_reg, params_dict, executor):
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        # ('finetune/api_based_finetune.ipynb', {}),  # 鉴权不一致
        # ('finetune/finetune_with_bos_and_evaluate.ipynb', {}),  # 未通过
        ('finetune/trainer_finetune.ipynb', {}),
        # 24/26 APIError: api return error, req_id: 3838549625 code: 500001, msg: param invalid
        # ('finetune/trainer_finetune_event_resume.ipynb', {}),  # 鉴权不一致
    ]
)
def test_finetune(file_reg, params_dict, executor):
    executor.prepare(file_reg, params_dict)
    executor.run()


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('wandb/wandb.ipynb', {}),  # 未通过
    ]
)
def test_wandb(file_reg, params_dict, executor):
    executor.prepare(file_reg, params_dict)
    executor.run()
